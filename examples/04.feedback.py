from ai_agent_toolbox import Toolbox, XMLParser, XMLPromptFormatter, FeedbackBuffer
from examples.util import anthropic_llm_call

# Initialize components
feedback = FeedbackBuffer(capacity=3)
toolbox = Toolbox()
parser = XMLParser(tag="tool")
formatter = XMLPromptFormatter(tag="tool").with_feedback(feedback)

# Simple search tool returning formatted result
toolbox.add_tool(
    name="search",
    fn=lambda topic: f"3 recent papers on {topic} (2024)",
    args={"topic": "string"},
    description="Search academic databases"
)

# Agent workflow
query = "AI safety research"
for cycle in range(3):
    # Build dynamic prompt
    user_prompt = f"""{formatter.format_feedback()}
Please research: {query}"""

    response = anthropic_llm_call(
        system_prompt=f"Research assistant. Use available tools.\n{formatter.usage_prompt(toolbox)}",
        prompt=user_prompt
    )
    
    # Execute tools and capture results
    findings = []
    events = parser.parse(response)
    for event in events:
        if event.is_tool_call:
            result = toolbox.use(event)
            if result:
                findings.append(result)
    
    # Store results in feedback buffer
    if findings:
        feedback.add("\n".join(findings))
        query = "Based on these findings, suggest next research direction"