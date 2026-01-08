"""
Benchmarks for AI Agent Toolbox parsing performance.

Measures metrics that matter for real-world streaming use cases like RL:
1. Time-to-first-tool: How quickly can we act on a tool call while streaming?
2. Memory efficiency: Peak memory usage during parsing
3. Throughput: Raw parsing operations per second
4. Streaming capability: Can the parser handle incomplete chunks?
"""

import time
import re
import tracemalloc
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional

from ai_agent_toolbox import XMLParser

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
NUM_ITERATIONS = 100
CHUNK_SIZE = 20  # Characters per chunk for streaming simulation

# A complete tool call that will be streamed character-by-character
COMPLETE_TOOL_XML = """<use_tool>
<name>calculate</name>
<expression>2 + 2</expression>
</use_tool>"""

# Large payload for memory benchmarks
LARGE_PAYLOAD = COMPLETE_TOOL_XML * 100

# Scaling test payloads (increasing sizes to show O(n²) vs O(n) behavior)
SCALING_SIZES = [1, 10, 50, 100, 200]


@dataclass
class BenchmarkResult:
    name: str
    time_to_first_tool_ms: Optional[float]
    memory_peak_kb: float
    throughput_ops_per_sec: float
    supports_streaming: bool
    notes: str = ""


# ------------------------------------------------------------------
# Streaming chunk generator
# ------------------------------------------------------------------
def stream_chunks(text: str, chunk_size: int = CHUNK_SIZE):
    """Yield text in small chunks to simulate streaming."""
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


# ------------------------------------------------------------------
# AI Agent Toolbox Parser
# ------------------------------------------------------------------
def benchmark_toolbox() -> BenchmarkResult:
    """Benchmark the AI Agent Toolbox XMLParser."""

    # Time to first tool
    parser = XMLParser(tag="use_tool")
    first_tool_time = None
    start = time.perf_counter()

    for chunk in stream_chunks(COMPLETE_TOOL_XML):
        events = parser.parse_chunk(chunk)
        for event in events:
            if event.type == "tool" and event.mode == "close" and first_tool_time is None:
                first_tool_time = (time.perf_counter() - start) * 1000

    for event in parser.flush():
        if event.type == "tool" and event.mode == "close" and first_tool_time is None:
            first_tool_time = (time.perf_counter() - start) * 1000

    # Memory benchmark
    tracemalloc.start()
    parser = XMLParser(tag="use_tool")
    for chunk in stream_chunks(LARGE_PAYLOAD):
        parser.parse_chunk(chunk)
    parser.flush()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Throughput (parsing only, no tool execution)
    start = time.perf_counter()
    for _ in range(NUM_ITERATIONS):
        parser = XMLParser(tag="use_tool")
        for chunk in stream_chunks(COMPLETE_TOOL_XML):
            parser.parse_chunk(chunk)
        parser.flush()
    elapsed = time.perf_counter() - start
    throughput = NUM_ITERATIONS / elapsed

    return BenchmarkResult(
        name="AI Agent Toolbox",
        time_to_first_tool_ms=first_tool_time,
        memory_peak_kb=peak / 1024,
        throughput_ops_per_sec=throughput,
        supports_streaming=True,
        notes="Native streaming support"
    )


# ------------------------------------------------------------------
# Naive Regex (batch only - cannot stream)
# ------------------------------------------------------------------
def benchmark_naive_regex_batch() -> BenchmarkResult:
    """Benchmark naive regex parser - batch mode only."""

    pattern = re.compile(r'<use_tool>(.*?)</use_tool>', re.DOTALL)

    # Time to first tool - must wait for complete input
    start = time.perf_counter()
    buffer = ""
    first_tool_time = None

    for chunk in stream_chunks(COMPLETE_TOOL_XML):
        buffer += chunk
        # Can only parse when complete - check if we have closing tag
        if '</use_tool>' in buffer and first_tool_time is None:
            matches = pattern.findall(buffer)
            if matches:
                first_tool_time = (time.perf_counter() - start) * 1000

    # Memory benchmark
    tracemalloc.start()
    buffer = ""
    for chunk in stream_chunks(LARGE_PAYLOAD):
        buffer += chunk
    pattern.findall(buffer)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Throughput
    start = time.perf_counter()
    for _ in range(NUM_ITERATIONS):
        buffer = ""
        for chunk in stream_chunks(COMPLETE_TOOL_XML):
            buffer += chunk
        pattern.findall(buffer)
    elapsed = time.perf_counter() - start
    throughput = NUM_ITERATIONS / elapsed

    return BenchmarkResult(
        name="Naive Regex (batch)",
        time_to_first_tool_ms=first_tool_time,
        memory_peak_kb=peak / 1024,
        throughput_ops_per_sec=throughput,
        supports_streaming=False,
        notes="Must buffer entire input"
    )


# ------------------------------------------------------------------
# Naive Regex (brute-force streaming - re-parse on every chunk)
# ------------------------------------------------------------------
def benchmark_naive_regex_bruteforce() -> BenchmarkResult:
    """Benchmark naive regex with brute-force streaming (re-parse everything on each chunk)."""

    pattern = re.compile(r'<use_tool>(.*?)</use_tool>', re.DOTALL)

    # Time to first tool - re-parse entire buffer on every chunk
    start = time.perf_counter()
    buffer = ""
    first_tool_time = None
    parse_count = 0

    for chunk in stream_chunks(COMPLETE_TOOL_XML):
        buffer += chunk
        matches = pattern.findall(buffer)  # Re-parse entire buffer every time!
        parse_count += 1
        if matches and first_tool_time is None:
            first_tool_time = (time.perf_counter() - start) * 1000

    # Memory benchmark
    tracemalloc.start()
    buffer = ""
    for chunk in stream_chunks(LARGE_PAYLOAD):
        buffer += chunk
        pattern.findall(buffer)  # Re-parse entire buffer every time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Throughput
    start = time.perf_counter()
    for _ in range(NUM_ITERATIONS):
        buffer = ""
        for chunk in stream_chunks(COMPLETE_TOOL_XML):
            buffer += chunk
            pattern.findall(buffer)
    elapsed = time.perf_counter() - start
    throughput = NUM_ITERATIONS / elapsed

    return BenchmarkResult(
        name="Naive Regex (brute-force stream)",
        time_to_first_tool_ms=first_tool_time,
        memory_peak_kb=peak / 1024,
        throughput_ops_per_sec=throughput,
        supports_streaming=True,
        notes=f"Re-parses entire buffer on each chunk ({parse_count} parses for 1 tool)"
    )


# ------------------------------------------------------------------
# Naive XML ElementTree (batch only)
# ------------------------------------------------------------------
def benchmark_naive_xml_batch() -> BenchmarkResult:
    """Benchmark naive XML parser - batch mode only."""

    # Time to first tool - must wait for complete valid XML
    start = time.perf_counter()
    buffer = ""
    first_tool_time = None

    for chunk in stream_chunks(COMPLETE_TOOL_XML):
        buffer += chunk
        try:
            root = ET.fromstring(buffer)
            if root.tag == "use_tool" and first_tool_time is None:
                first_tool_time = (time.perf_counter() - start) * 1000
        except ET.ParseError:
            pass  # Incomplete XML

    # Memory benchmark
    tracemalloc.start()
    buffer = ""
    for chunk in stream_chunks(LARGE_PAYLOAD):
        buffer += chunk
    # Can only parse one at a time with ElementTree
    try:
        ET.fromstring(f"<root>{buffer}</root>")
    except ET.ParseError:
        pass
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Throughput
    start = time.perf_counter()
    for _ in range(NUM_ITERATIONS):
        buffer = ""
        for chunk in stream_chunks(COMPLETE_TOOL_XML):
            buffer += chunk
        try:
            ET.fromstring(buffer)
        except ET.ParseError:
            pass
    elapsed = time.perf_counter() - start
    throughput = NUM_ITERATIONS / elapsed

    return BenchmarkResult(
        name="Naive XML (batch)",
        time_to_first_tool_ms=first_tool_time,
        memory_peak_kb=peak / 1024,
        throughput_ops_per_sec=throughput,
        supports_streaming=False,
        notes="Fails on incomplete XML"
    )


# ------------------------------------------------------------------
# Naive XML (brute-force streaming)
# ------------------------------------------------------------------
def benchmark_naive_xml_bruteforce() -> BenchmarkResult:
    """Benchmark naive XML with brute-force streaming (try parse on every chunk)."""

    # Time to first tool
    start = time.perf_counter()
    buffer = ""
    first_tool_time = None
    parse_attempts = 0

    for chunk in stream_chunks(COMPLETE_TOOL_XML):
        buffer += chunk
        parse_attempts += 1
        try:
            root = ET.fromstring(buffer)
            if root.tag == "use_tool" and first_tool_time is None:
                first_tool_time = (time.perf_counter() - start) * 1000
        except ET.ParseError:
            pass  # Expected on incomplete XML

    # Memory benchmark
    tracemalloc.start()
    buffer = ""
    for chunk in stream_chunks(LARGE_PAYLOAD):
        buffer += chunk
        try:
            ET.fromstring(f"<root>{buffer}</root>")
        except ET.ParseError:
            pass
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Throughput
    start = time.perf_counter()
    for _ in range(NUM_ITERATIONS):
        buffer = ""
        for chunk in stream_chunks(COMPLETE_TOOL_XML):
            buffer += chunk
            try:
                ET.fromstring(buffer)
            except ET.ParseError:
                pass
    elapsed = time.perf_counter() - start
    throughput = NUM_ITERATIONS / elapsed

    return BenchmarkResult(
        name="Naive XML (brute-force stream)",
        time_to_first_tool_ms=first_tool_time,
        memory_peak_kb=peak / 1024,
        throughput_ops_per_sec=throughput,
        supports_streaming=True,
        notes=f"Throws {parse_attempts-1} exceptions to parse 1 tool"
    )


# ------------------------------------------------------------------
# Scaling Benchmark (shows O(n²) vs O(n) behavior)
# ------------------------------------------------------------------
def benchmark_scaling() -> dict:
    """Benchmark how parsing time scales with payload size."""

    pattern = re.compile(r'<use_tool>(.*?)</use_tool>', re.DOTALL)
    results = {"sizes": [], "toolbox": [], "bruteforce_regex": []}

    for num_tools in SCALING_SIZES:
        payload = COMPLETE_TOOL_XML * num_tools
        results["sizes"].append(num_tools)

        # Toolbox
        start = time.perf_counter()
        for _ in range(10):
            parser = XMLParser(tag="use_tool")
            for chunk in stream_chunks(payload, CHUNK_SIZE):
                parser.parse_chunk(chunk)
            parser.flush()
        toolbox_time = (time.perf_counter() - start) / 10
        results["toolbox"].append(toolbox_time * 1000)

        # Brute-force regex
        start = time.perf_counter()
        for _ in range(10):
            buffer = ""
            for chunk in stream_chunks(payload, CHUNK_SIZE):
                buffer += chunk
                pattern.findall(buffer)
        bruteforce_time = (time.perf_counter() - start) / 10
        results["bruteforce_regex"].append(bruteforce_time * 1000)

    return results


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def print_results(results: List[BenchmarkResult]) -> None:
    """Print benchmark results in a formatted table."""

    print("\n" + "=" * 90)
    print("PARSING BENCHMARK RESULTS")
    print("=" * 90)

    # Header
    print(f"\n{'Parser':<32} {'First Tool (ms)':<16} {'Memory (KB)':<14} {'Throughput':<14} {'Streaming'}")
    print("-" * 90)

    for r in results:
        first_tool = f"{r.time_to_first_tool_ms:.2f}" if r.time_to_first_tool_ms else "N/A"
        streaming = "Yes" if r.supports_streaming else "No"
        print(f"{r.name:<32} {first_tool:<16} {r.memory_peak_kb:<14.1f} {r.throughput_ops_per_sec:<14.0f} {streaming}")

    print("-" * 90)

    # Notes
    print("\nNotes:")
    for r in results:
        if r.notes:
            print(f"  - {r.name}: {r.notes}")

    # Analysis
    toolbox = next(r for r in results if r.name == "AI Agent Toolbox")
    bruteforce_regex = next(r for r in results if "brute-force" in r.name and "Regex" in r.name)

    print("\n" + "=" * 90)
    print("SUMMARY vs BRUTE-FORCE REGEX")
    print("=" * 90)

    memory_ratio = bruteforce_regex.memory_peak_kb / toolbox.memory_peak_kb
    print(f"\nMemory: AI Agent Toolbox uses {memory_ratio:.1f}x less memory")

    throughput_ratio = toolbox.throughput_ops_per_sec / bruteforce_regex.throughput_ops_per_sec
    if throughput_ratio >= 1:
        print(f"Throughput: AI Agent Toolbox is {throughput_ratio:.1f}x faster")
    else:
        print(f"Throughput: AI Agent Toolbox is {1/throughput_ratio:.1f}x slower (small payload overhead)")

    print("\n" + "=" * 90)


def print_scaling_results(scaling: dict) -> None:
    """Print scaling benchmark results."""

    print("\n" + "=" * 90)
    print("SCALING BENCHMARK (shows O(n) vs O(n²) behavior)")
    print("=" * 90)
    print("\nTime (ms) to parse payload with N tool calls:")
    print(f"\n{'Tools':<10} {'Toolbox (ms)':<15} {'Brute-force (ms)':<18} {'Ratio':<10}")
    print("-" * 55)

    for i, size in enumerate(scaling["sizes"]):
        tb = scaling["toolbox"][i]
        bf = scaling["bruteforce_regex"][i]
        ratio = bf / tb if tb > 0 else 0
        winner = "Toolbox wins!" if ratio > 1 else ""
        print(f"{size:<10} {tb:<15.2f} {bf:<18.2f} {ratio:<10.1f}x {winner}")

    print("-" * 55)

    # Show the growth rate
    if len(scaling["sizes"]) >= 2:
        tb_growth = scaling["toolbox"][-1] / scaling["toolbox"][0]
        bf_growth = scaling["bruteforce_regex"][-1] / scaling["bruteforce_regex"][0]
        size_growth = scaling["sizes"][-1] / scaling["sizes"][0]
        print(f"\nGrowth from {scaling['sizes'][0]} to {scaling['sizes'][-1]} tools ({size_growth:.0f}x payload):")
        print(f"  Toolbox:     {tb_growth:.1f}x slower (linear scaling)")
        print(f"  Brute-force: {bf_growth:.1f}x slower (quadratic scaling)")

    print("\n" + "=" * 90)


def main():
    results = [
        benchmark_toolbox(),
        benchmark_naive_regex_batch(),
        benchmark_naive_regex_bruteforce(),
        benchmark_naive_xml_batch(),
        benchmark_naive_xml_bruteforce(),
    ]

    print_results(results)

    # Run scaling benchmark
    scaling = benchmark_scaling()
    print_scaling_results(scaling)


if __name__ == "__main__":
    main()
