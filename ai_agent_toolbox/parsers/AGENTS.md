# Parser package guidelines

- Place each concrete parser in its own module named ``<format>_parser.py`` under a dedicated subpackage (for example, ``xml/xml_parser.py``).
- Keep parser modules narrowly focused; if a parser grows beyond ~200 lines split shared logic into helpers under ``utils.py`` or a new private module.
- When introducing a new parser variant, expose it via ``ai_agent_toolbox/__init__.py`` so that ``from ai_agent_toolbox import NewParser`` continues to work.
- Reuse ``parser.py`` for abstract base classes and ensure helpers shared across parsers stay in ``utils.py`` to avoid duplication.
