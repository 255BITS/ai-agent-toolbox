# benchmarks/parsing_benchmarks.py

import asyncio
import re
import xml.etree.ElementTree as ET

# Import your toolbox‐based classes.
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter

# ------------------------------------------------------------------
# Sample Data & Async Stream Simulation
# ------------------------------------------------------------------

# A sample XML chunk that your custom parser is designed to process.
# Adjust this XML to reflect realistic input for your parser.
SAMPLE_CHUNK = """
<use_tool>
<name>yeeting</name>
<thoughts>Example content</thoughts>
</use_tool>
"""

async def dummy_stream(num_chunks=10):
    """
    Simulate an asynchronous stream yielding the same XML chunk repeatedly.
    """
    for _ in range(num_chunks):
        yield SAMPLE_CHUNK
        await asyncio.sleep(0)  # Yield control to simulate async behavior

# Dummy tool functions to avoid I/O overhead during benchmarks.
def dummy_use(event):
    pass

async def dummy_use_async(event):
    pass

# ------------------------------------------------------------------
# ASV Benchmark Suite
# ------------------------------------------------------------------

class ParsingBenchmarks:
    """
    ASV benchmark suite to compare:
      - Your custom parser using XMLParser (integrated with Toolbox)
      - A naive regex parser (for <use_tool> content)
      - A naive XML parser using xml.etree.ElementTree
    """

    def setup(self):
        # Create a dedicated event loop for async benchmarks.
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # Number of chunks per iteration and iterations overall.
        self.num_chunks = 10
        self.num_iterations = 100

    def teardown(self):
        self.loop.close()

    # -----------------------------------------------------------
    # 1. Custom Parser Benchmark (Using XMLParser, Toolbox, etc.)
    # -----------------------------------------------------------
    def time_custom_parser(self):
        """
        Benchmark the integrated, async processing using your custom XMLParser.
        This simulates the work done in your main() function.
        """
        async def run():
            # Set up your workbench.
            toolbox = Toolbox()
            # Replace the yeeting function with a dummy to avoid I/O overhead.
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

            # Compose system prompt (even though its content isn’t used in parsing).
            system = "You are a yeeting AI. You have interesting yeets."
            prompt = "Yeet about something interesting."
            system += formatter.usage_prompt(toolbox)

            # Simulate processing multiple batches.
            for _ in range(self.num_iterations):
                async for chunk in dummy_stream(self.num_chunks):
                    # Parse the incoming chunk.
                    for event in parser.parse_chunk(chunk):
                        await toolbox.use_async(event)
                # Process any remaining events.
                for event in parser.flush():
                    toolbox.use(event)
        self.loop.run_until_complete(run())

    # -----------------------------------------------------------
    # 2. Naive Regex Parser Benchmark
    # -----------------------------------------------------------
    def time_naive_regex_parser(self):
        """
        Benchmark a naive parser using a regex to extract content within <use_tool> tags.
        """
        # Define the naive regex parser function.
        def naive_regex_parser(data):
            # This pattern captures any content between <use_tool> and </use_tool>,
            # including newlines (thanks to DOTALL).
            pattern = re.compile(r'<use_tool>(.*?)</use_tool>', re.DOTALL)
            return pattern.findall(data)

        async def run():
            for _ in range(self.num_iterations):
                async for chunk in dummy_stream(self.num_chunks):
                    naive_regex_parser(chunk)
        self.loop.run_until_complete(run())

    # -----------------------------------------------------------
    # 3. Naive XML Parser Benchmark (ElementTree)
    # -----------------------------------------------------------
    def time_naive_xml_parser(self):
        """
        Benchmark a naive parser that uses xml.etree.ElementTree to parse the XML.
        """
        def naive_xml_parser(data):
            try:
                root = ET.fromstring(data)
            except ET.ParseError:
                return None
            # In this simple case, if the root tag is 'use_tool', return its text.
            if root.tag == 'use_tool':
                return root.text
            return None

        async def run():
            for _ in range(self.num_iterations):
                async for chunk in dummy_stream(self.num_chunks):
                    naive_xml_parser(chunk)
        self.loop.run_until_complete(run())
