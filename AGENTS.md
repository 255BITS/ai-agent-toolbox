# Contribution Guidelines

## Module layout
- Keep modules focused and compact. If an implementation grows beyond ~250 lines (including helper functions), look for opportunities to split it into smaller pieces or extract shared helpers.
- New classes should live in their own module. Name the module after the class using ``snake_case`` (for example, ``XMLPromptFormatter`` lives in ``xml_prompt_formatter.py``).
- Lightweight helper functions or dataclasses that exist solely to support the primary class may stay in the same module, but avoid defining multiple top-level classes with independent responsibilities in a single file.

## Package organisation
- Production code lives under ``ai_agent_toolbox``. Tests and examples stay in their existing top-level folders.
- Parsers belong in ``ai_agent_toolbox/parsers`` and prompt formatters in ``ai_agent_toolbox/formatters``. Each specialised format (XML, JSON, Markdown, etc.) has its own subpackage; add new formats by creating a matching folder and module pair.
- Utility-only modules should use a ``utils.py`` suffix (for example, ``ai_agent_toolbox/parsers/utils.py``) and keep their APIs narrowly scoped.

## Scoped guidelines
Additional notes for particular subpackages are documented in nested ``AGENTS.md`` files (see ``ai_agent_toolbox/parsers`` and ``ai_agent_toolbox/formatters``).
