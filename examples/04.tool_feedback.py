import json
import requests
from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter
from examples.util import anthropic_llm_call

def arxiv_search(topic, max_results=3):
    """
    Search arXiv for recent papers on a given topic.
    Returns a simple bullet-list of up to `max_results` paper titles.
    """
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{topic}",
        "start": 0,
        "max_results": max_results
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return f"Failed to reach arXiv: {response.status_code}"

    # Very simple parse for demonstration (extracting first few titles)
    # For robust usage, consider using something like 'feedparser'.
    content = response.text
    entries = content.split("<entry>")
    titles = []
    for entry in entries[1:]:  # skip the feed metadata in the first chunk
        start_idx = entry.find("<title>")
        end_idx = entry.find("</title>")
        if start_idx != -1 and end_idx != -1:
            title = entry[start_idx + 7:end_idx].strip()
            titles.append(title)

    if not titles:
        return "No results found."

    return "\n".join(f"- {t}" for t in titles)


# Initialize the toolbox with our arXiv search tool
toolbox = Toolbox()
toolbox.add_tool(
    name="search",
    fn=arxiv_search,
    args={
        "topic": {
            "type": "string",
            "description": "The topic to search on arXiv"
        }
    },
    description="Search academic databases via arXiv"
)

# Parser and prompt formatter
parser = XMLParser(tag="tool")
formatter = XMLPromptFormatter(tag="tool")

# We'll store each cycle's feedback in a list
feedback_history = []

# Initial query from the user
query = "AI agent researcher"

# Run multiple query cycles
for cycle in range(3):
    print(f"=== CYCLE {cycle + 1} ===")
    
    # Use the last feedback if it exists, otherwise start with nothing
    last_feedback = feedback_history[-1] if feedback_history else ""
    user_prompt = f"{last_feedback}\nPlease research: {query}"
    print("User prompt:\n", user_prompt, "\n")
    print()

    # Call your LLM (Anthropic, in this example)
    response = anthropic_llm_call(
        system_prompt=(
            "You are a research assistant. "
            "You can use the following tools to help:\n"
            + formatter.usage_prompt(toolbox)
        ),
        prompt=user_prompt
    )
    print("LLM response:\n", response, "\n")
    print()

    # Parse out any <tool> usage and execute
    events = parser.parse(response)
    if events:
        print("Tool calls parsed:")
    else:
        print("No tool calls found in this cycle.\n")

    findings = []
    for event in events:
        if event.is_tool_call:
            print(f"  Using tool: {event.tool.name} with args {json.dumps(event.tool.args)}")
        tool_response = toolbox.use(event)
        if tool_response:
            findings.append(tool_response.result)
            print("  Tool output:")
            print("  ", tool_response.result, "\n")

    # If we got any findings, store them for the next cycle
    if findings:
        feedback_chunk = "\n".join(findings)
        feedback_history.append(feedback_chunk)

    # Update the query for the next round
    query = "Based on these findings, suggest the next research direction"

print("=== FINAL FEEDBACK ACROSS ALL CYCLES ===\n")
for i, fb in enumerate(feedback_history, start=1):
    print(f"Cycle {i} feedback:\n{fb}\n---\n")
