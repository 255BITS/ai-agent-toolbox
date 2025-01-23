from ai_agent_toolbox import Toolbox, FlatXMLParser, FlatXMLPromptFormatter
from examples.util import anthropic_llm_call

# This example shows a write-only Tool(no feedback) writing to an environment. The state of the Environment is shared with the LLM.
class ShoppingEnvironment:
    """Simple environment to track shopping list items"""
    def __init__(self):
        self.items = []
    
    def add_item(self, item: str):
        """Add an item to the shopping list"""
        self.items.append(item)
    
    def __str__(self):
        return f"Shopping List: {', '.join(self.items) if self.items else 'empty'}"

# Initialize environment and agent settings
env = ShoppingEnvironment()
MAX_ITEMS = 3

# Set up agent components
toolbox = Toolbox()
parser = FlatXMLParser("add_item")  # Watch for <add_item> tags
formatter = FlatXMLPromptFormatter(tag="add_item")

# Define and register the write-only tool
def add_item(content: str):
    """Tool function that modifies the environment"""
    env.add_item(content.strip())
    print(f"Added: {content}")

toolbox.add_tool(
    name="add_item",
    fn=add_item,
    args={
        "content": {
            "type": "string",
            "description": "Item to add to the shopping list"
        }
    },
    description="Add items to the shopping list"
)

# Build system prompt with tool documentation
system_prompt = f"You are a shopping assistant. Add items until there are {MAX_ITEMS}.\n"
system_prompt += formatter.usage_prompt(toolbox)

print("System prompt:", system_prompt)

# Agent interaction loop
while len(env.items) < MAX_ITEMS:
    # Create state-aware prompt
    user_prompt = f"Current list ({len(env.items)}/{MAX_ITEMS}): {', '.join(env.items) if env.items else 'empty'}. What item should we add next?"

    # Get agent response
    response = anthropic_llm_call(
        system_prompt=system_prompt,
        prompt=user_prompt,
    )

    # Process and execute tool calls
    events = parser.parse(response)
    for event in events:
        if event.is_tool_call and event.tool.name == "add_item":
            toolbox.use(event)

print(env)
print("✅ Shopping list complete!")
