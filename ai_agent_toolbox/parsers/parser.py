from typing import List
from ai_agent_toolbox.parser_event import ParserEvent

class Parser:
    def parse(self, text: str) -> List[ParserEvent]:
        pass

    def parse_chunk(self, chunk: str) -> List[ParserEvent]:
        pass

    def flush(self) -> List[ParserEvent]:
        pass
