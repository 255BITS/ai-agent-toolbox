# Basic Usage Guide

## Tool Definition

Tools are the core concept in AI Agent Toolbox. A tool is a function that can be called by an AI model through a structured interface.

### Creating Tools

```python
def search_database(query: str, limit: int = 10):
    # Implementation
    return results

toolbox.add_tool(
    name="search",
    fn=search_database,
    args={
        "query": {
            "type": str,
            "description": "Search query string"
        },
        "limit": {
            "type": int,
            "description": "Maximum results to return",
            "default": 10
        }
    },
    description="Search the database for relevant information"
)
```
