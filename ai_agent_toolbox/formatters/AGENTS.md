# Formatter package guidelines

- Implement each concrete prompt formatter in its own module named ``<format>_prompt_formatter.py`` under the corresponding format subpackage (for example, ``json/json_prompt_formatter.py``).
- Keep formatter modules lean; if you find yourself adding reusable helper logic, move it into ``prompt_formatter.py`` or a dedicated utility module instead of introducing multiple formatter classes per file.
- Update ``ai_agent_toolbox/__init__.py`` and ``ai_agent_toolbox/formatters/__init__.py`` when adding a formatter so it is importable from the package root.
