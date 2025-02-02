import asyncio
import time
import re
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

# Import your toolbox-based classes.
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter

# ------------------------------------------------------------------
# Configuration for the benchmark
# ------------------------------------------------------------------
NUM_ITERATIONS = 100  # Number of iterations for each benchmark.
NUM_CHUNKS = 10       # Number of chunks per iteration.

# A sample XML chunk that the parsers will process.
SAMPLE_CHUNK = """
<use_tool>
<name>yeeting</name>
<thoughts>Example content</thoughts>
</use_tool>
"""



async def dummy_stream(num_chunks=NUM_CHUNKS):
    """
    Simulate an asynchronous stream yielding the same XML chunk repeatedly.
    """
    for _ in range(num_chunks):
        yield SAMPLE_CHUNK
        await asyncio.sleep(0)  # Yield control to mimic async behavior.

# ------------------------------------------------------------------
# Benchmark Functions
# ------------------------------------------------------------------

async def run_custom_parser(num_iterations=NUM_ITERATIONS, num_chunks=NUM_CHUNKS):
    """
    Benchmark using your AI Agent Toolbox-based parser.
    Simulates the work done in your production async function.
    """
    # Set up your workbench.
    toolbox = Toolbox()

    # Dummy asynchronous function to avoid I/O overhead.
    async def yeeting(thoughts=""):
        pass

    toolbox.add_tool(
        name="yeeting",
        fn=yeeting,
        args={
            "thoughts": {
                "type": "string", 
                "description": "Anything you want to yeet about"
            }
        },
        description="For yeeting out loud"
    )

    parser = XMLParser(tag="use_tool")
    formatter = XMLPromptFormatter(tag="use_tool")

    # Compose the system prompt (its content isn’t critical for the benchmark).
    system = "You are a yeeting AI. You have interesting yeets."
    prompt = "Yeet about something interesting."
    system += formatter.usage_prompt(toolbox)

    # Process the async stream for a number of iterations.
    for _ in range(num_iterations):
        async for chunk in dummy_stream(num_chunks):
            for event in parser.parse_chunk(chunk):
                await toolbox.use_async(event)
        # Process any remaining events.
        for event in parser.flush():
            toolbox.use(event)

async def run_naive_regex_parser(num_iterations=NUM_ITERATIONS, num_chunks=NUM_CHUNKS):
    """
    Benchmark a naive parser that uses regex to extract content from <use_tool> tags.
    """
    # Compile the pattern once outside the loop.
    pattern = re.compile(r'<use_tool>(.*?)</use_tool>', re.DOTALL)

    def naive_regex_parser(data):
        results = []
        # Use finditer to capture matches with positional information
        for match in pattern.finditer(data):
            start_pos = match.start()   # Start position of the entire match
            end_pos = match.end()       # End position of the entire match
            content = match.group(1)    # Captured content between the tags
            results.append((content, start_pos, end_pos))
        return results

    for _ in range(num_iterations):
        total = ""
        async for chunk in dummy_stream(num_chunks):
            total += chunk
            naive_regex_parser(total)

async def run_naive_xml_parser(num_iterations=NUM_ITERATIONS, num_chunks=NUM_CHUNKS):
    """
    Benchmark a naive parser that uses xml.etree.ElementTree to parse the XML.
    """
    def naive_xml_parser(data):
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            return None
        # If the root tag is 'use_tool', process its text.
        if root.tag == "use_tool":
            result = root.text
            for elem in root.iter():
                pass
            return result
        return None

    for _ in range(num_iterations):
        total = ""
        async for chunk in dummy_stream(num_chunks):
            total += chunk
            naive_xml_parser(total)

# ------------------------------------------------------------------
# Main: Run Benchmarks & Create Chart
# ------------------------------------------------------------------

async def main():
    # Measure the time for the custom (Toolbox) parser.
    start = time.perf_counter()
    await run_custom_parser()
    time_custom = time.perf_counter() - start

    # Measure the time for the naive XML parser.
    start = time.perf_counter()
    await run_naive_xml_parser()
    time_naive_xml = time.perf_counter() - start

    # Measure the time for the naive regex parser.
    start = time.perf_counter()
    await run_naive_regex_parser()
    time_naive_regex = time.perf_counter() - start

    # Print benchmark results.
    print("Benchmark results (in seconds):")
    print(f"AI Agent Toolbox: {time_custom:.4f}")
    print(f"Naive XML:        {time_naive_xml:.4f}")
    print(f"Naive regex:      {time_naive_regex:.4f}")

    # ------------------------------------------------------------------
    # Create the bar chart with enhanced styling.
    # ------------------------------------------------------------------

    times = [time_custom, time_naive_xml, time_naive_regex]
    labels = ["AI Agent Toolbox", "Naive XML", "Naive regex"]
    colors = ['#2ecc71', '#f1c40f', '#e74c3c']  # A refined color palette.

    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    bars = ax.bar(labels, times, color=colors, edgecolor='black', width=0.6)

    # Set chart title and axis labels with enhanced fonts.
    ax.set_title("Parsing Benchmark Results\n(Lower is Better)", fontsize=24, pad=20, fontweight='bold')
    ax.set_ylabel("Time (seconds)", fontsize=18)
    ax.set_xlabel("Parsing Techniques", fontsize=18)

    # Annotate each bar with its timing value.
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:.2f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 8),  # vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=16, fontweight='bold')

    # Add gridlines for better readability.
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)  # Ensure gridlines appear behind the bars.

    # Finalize layout and display the figure.
    plt.tight_layout()
    plt.savefig("tool_parsing_benchmark.png", dpi=100)
    plt.show()

if __name__ == "__main__":
    # Run the async main function.
    asyncio.run(main())
