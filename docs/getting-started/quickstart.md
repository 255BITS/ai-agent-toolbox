# Quick Start Guide

## Basic Usage

1. Create a Toolbox:
```python
from ai_agent_toolbox import Toolbox
from ai_agent_toolbox.parsers import XMLParser

toolbox = Toolbox()
parser = XMLParser(tag="use_tool")
```

2. Define and Add Tools:
```python
def thinking(thoughts=""):
    print(f"Thinking: {thoughts}")

toolbox.add_tool(
    name="thinking",
    fn=thinking,
    args={
        "thoughts": {
            "type": str,
            "description": "Thoughts to process"
        }
    },
    description="For thinking out loud"
)
