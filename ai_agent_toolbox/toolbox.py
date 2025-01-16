from typing import Callable, Dict, Any

class Toolbox:
    """
    Manages tools for an AI agent.
    """

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def add_tool(self, name: str, args: Dict[str, str], description: str, func: Callable = None):
        """
        Add a tool with its name, args, description, and optional behavior.
        """
        if name in self.tools:
            raise ValueError(f"Tool '{name}' is already defined.")

        self.tools[name] = {
            "args": args,
            "description": description,
            "func": func or self.default_behavior,
        }

    def default_behavior(self, **kwargs):
        """Default behavior if no function is provided."""
        return kwargs

    def validate_args(self, name: str, **kwargs):
        """Validate arguments for a given tool."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' is not defined.")

        tool_args = self.tools[name]["args"]
        for arg_name, arg_type in tool_args.items():
            if arg_name not in kwargs:
                raise ValueError(f"Missing argument '{arg_name}' for tool '{name}'.")

            if not isinstance(kwargs[arg_name], eval(arg_type)):
                raise ValueError(
                    f"Argument '{arg_name}' must be of type '{arg_type}' for tool '{name}'."
                )

    def use(self, event):
        """Use a tool based on the event."""
        tool_name = event.tool_name
        args = {arg_event.arg: arg_event.content for arg_event in event.args}

        self.validate_args(tool_name, **args)
        return self.tools[tool_name]["func"](**args)

    def list_tools(self):
        """List all tools with their descriptions."""
        return {name: tool["description"] for name, tool in self.tools.items()}

    def remove_tool(self, name: str):
        """Remove a tool by name."""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' is not defined.")

        del self.tools[name]
