from typing import Dict

class PromptFormatter:
    """Abstract base class for prompt formatters."""
    def format_prompt(self, tools: Dict[str, Dict[str, str]]) -> str:
        """Formats the prompt to describe available tools."""
        pass

    def usage_prompt(self, toolbox) -> str:
        """Generates a usage prompt from a Toolbox instance."""
        pass
