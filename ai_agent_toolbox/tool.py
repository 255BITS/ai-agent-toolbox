from typing import Any, Callable, Dict

class Tool:
    """Represents a tool with a name, arguments, and behavior."""

    def __init__(self, name: str, args: Dict[str, str], description: str, func: Callable[[Any], Any] = None):
        self.name = name
        self.args = args
        self.description = description
        self.func = func or self._default_behavior

    def execute(self, **kwargs):
        """Execute the tool's function with validated arguments."""
        self._validate_args(**kwargs)
        return self.func(**kwargs)

    def _validate_args(self, **kwargs):
        """Validate arguments against the expected types."""
        for arg_name, arg_type in self.args.items():
            if arg_name not in kwargs:
                raise ValueError(f"Missing argument '{arg_name}' for tool '{self.name}'.")

            if not isinstance(kwargs[arg_name], eval(arg_type)):
                raise ValueError(f"Argument '{arg_name}' must be of type '{arg_type}' for tool '{self.name}'.")

    def _default_behavior(self, **kwargs):
        """Default behavior: return provided arguments."""
        return kwargs

    def __repr__(self):
        return f"Tool(name='{self.name}', description='{self.description}', args={self.args})"
