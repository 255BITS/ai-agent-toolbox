from __future__ import annotations

from typing import List

from ai_agent_toolbox.parser_event import ParserEvent


class Parser:
    def parse(self, text: str) -> List[ParserEvent]:
        return self.parse_chunk(text) + self.flush()

    def parse_chunk(self, chunk: str) -> List[ParserEvent]:
        raise NotImplementedError

    def flush(self) -> List[ParserEvent]:
        raise NotImplementedError
