import json
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ai_agent_toolbox.parser_event import ParserEvent
from ai_agent_toolbox.tool_use import ToolUse
from ai_agent_toolbox.parsers.utils import TextEventStream
from ai_agent_toolbox.parsers.parser import Parser

from .tool_call_state import ToolCallState


class JSONParser(Parser):
    """Parser that understands OpenAI/Anthropic style JSON tool call payloads."""

    def __init__(self):
        self.buffer: str = ""
        self.events: List[ParserEvent] = []
        self.text_stream: TextEventStream = TextEventStream(
            lambda event: self.events.append(event)
        )

        # Tool call tracking
        self.tool_states: Dict[str, ToolCallState] = {}
        self.tool_lookup: Dict[Tuple[str, Any], str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse_chunk(self, chunk: str) -> List[ParserEvent]:
        """Parse a chunk of JSON data (useful for streaming)."""
        if not chunk:
            return []

        self.events = []
        self.buffer += chunk
        self._process_buffer(final=False)
        events = self.events
        self.events = []
        return events

    def flush(self) -> List[ParserEvent]:
        """Finalize the parser state when no more chunks are expected."""
        self.events = []
        if self.buffer:
            self._process_buffer(final=True)
            self.buffer = ""

        self._close_text_block()

        for state in list(self.tool_states.values()):
            self._finalize_tool_state(state)

        events = self.events
        self.events = []
        return events

    # ------------------------------------------------------------------
    # Buffer processing
    # ------------------------------------------------------------------
    def _process_buffer(self, final: bool) -> None:
        while True:
            result = self._extract_next_payload()
            if result is None:
                break

            payload, consumed = result
            if consumed == 0:
                break

            self.buffer = self.buffer[consumed:]

            if payload is None:
                continue

            self._handle_payload(payload)

        if final and self.buffer.strip():
            try:
                payload = json.loads(self.buffer)
            except json.JSONDecodeError:
                self.buffer = ""
                return
            self.buffer = ""
            self._handle_payload(payload)

    def _extract_next_payload(self) -> Optional[Tuple[Optional[Any], int]]:
        if not self.buffer:
            return None

        idx = 0
        length = len(self.buffer)

        while idx < length and self.buffer[idx] in " \t\r\n":
            idx += 1

        if idx >= length:
            return None

        if self.buffer[idx] == ":":
            newline = self.buffer.find("\n", idx)
            if newline == -1:
                return None
            return None, newline + 1

        if self.buffer.startswith("data:", idx):
            idx += 5
            while idx < length and self.buffer[idx] == " ":
                idx += 1

        if self.buffer.startswith("[DONE]", idx):
            consumed = idx + len("[DONE]")
            while consumed < length and self.buffer[consumed] in " \t\r\n":
                consumed += 1
            return None, consumed

        decoder = json.JSONDecoder()
        try:
            payload, raw_end = decoder.raw_decode(self.buffer[idx:])
        except json.JSONDecodeError:
            return None

        end_idx = idx + raw_end
        consumed = end_idx
        while consumed < length and self.buffer[consumed] in " \t\r\n":
            consumed += 1

        return payload, consumed

    # ------------------------------------------------------------------
    # Payload dispatch
    # ------------------------------------------------------------------
    def _handle_payload(self, payload: Any) -> None:
        if payload is None:
            return
        if isinstance(payload, list):
            for item in payload:
                self._handle_payload(item)
            return
        if isinstance(payload, str):
            self._stream_text(payload)
            return
        if isinstance(payload, dict):
            self._handle_dict(payload)

    def _handle_dict(self, data: Dict[str, Any]) -> None:
        data_type = data.get("type")

        if data_type == "content_block_start":
            self._handle_anthropic_start(data)
            return
        if data_type == "content_block_delta":
            self._handle_anthropic_delta(data)
            return
        if data_type == "content_block_stop":
            self._handle_anthropic_stop(data)
            return
        if data_type in {"response.completed", "response.error"}:
            self._finalize_all_tools()
            return

        if "choices" in data and isinstance(data["choices"], list):
            for choice in data["choices"]:
                self._handle_payload(choice)

        if "message" in data:
            self._handle_payload(data["message"])

        if "delta" in data:
            self._handle_payload(data["delta"])

        if "output" in data and isinstance(data["output"], list):
            for item in data["output"]:
                self._handle_payload(item)

        if "content" in data and isinstance(data["content"], list):
            for item in data["content"]:
                self._handle_payload(item)
        elif isinstance(data.get("content"), str):
            self._stream_text(data["content"])

        if "tool_calls" in data and isinstance(data["tool_calls"], list):
            for call in data["tool_calls"]:
                self._handle_tool_call(call)

        if "function_call" in data and isinstance(data["function_call"], dict):
            payload = {"type": "function", "function": data["function_call"]}
            if "id" in data:
                payload["id"] = data["id"]
            if "index" in data:
                payload["index"] = data["index"]
            self._handle_tool_call(payload)

        if data.get("finish_reason") == "tool_calls":
            self._finalize_all_tools()

        if isinstance(data.get("delta"), str):
            self._stream_text(data["delta"])

        if isinstance(data.get("text"), str) and data_type not in {"tool_call", "function", "tool_use"}:
            self._stream_text(data["text"])

        if data_type in {"tool_call", "function", "tool_use"} or "function" in data or "arguments" in data:
            self._handle_tool_call(data)

    # ------------------------------------------------------------------
    # Anthropic helpers
    # ------------------------------------------------------------------
    def _handle_anthropic_start(self, data: Dict[str, Any]) -> None:
        block = data.get("content_block", {}) or {}
        if block.get("type") != "tool_use":
            # Non tool blocks can include text; handle via delta events.
            return

        payload = {
            "type": "tool_use",
            "id": block.get("id"),
            "name": block.get("name"),
        }
        if "index" in data:
            payload["index"] = data["index"]
        if "input" in block:
            payload["input"] = block["input"]

        state = self._get_or_create_tool_state(payload)
        if block.get("name"):
            state.name = block["name"]
        self._ensure_tool_created(state)

        if isinstance(block.get("input"), dict) and block["input"]:
            serialized = json.dumps(block["input"])
            self._append_tool_arguments(state, serialized)
            self._finalize_tool_state(state)

    def _handle_anthropic_delta(self, data: Dict[str, Any]) -> None:
        delta = data.get("delta", {}) or {}
        delta_type = delta.get("type")

        if delta_type == "input_json":
            partial = delta.get("partial_json", "")
            if partial:
                state = self._get_or_create_tool_state({
                    "type": "tool_use",
                    "index": data.get("index"),
                })
                self._append_tool_arguments(state, partial)
            return

        text = delta.get("text")
        if isinstance(text, str):
            self._stream_text(text)

    def _handle_anthropic_stop(self, data: Dict[str, Any]) -> None:
        state = self._find_tool_state([
            ("index", data.get("index")),
        ])
        if state:
            self._finalize_tool_state(state)

    # ------------------------------------------------------------------
    # Tool state helpers
    # ------------------------------------------------------------------
    def _handle_tool_call(self, call: Dict[str, Any]) -> None:
        if not isinstance(call, dict):
            return

        state = self._get_or_create_tool_state(call)

        if not state.name:
            name = call.get("name")
            if not name:
                function = call.get("function")
                if isinstance(function, dict):
                    name = function.get("name")
            if name:
                state.name = name
        self._ensure_tool_created(state)

        function = call.get("function")
        if isinstance(function, dict):
            arguments = function.get("arguments")
            self._ingest_arguments(state, arguments)

        if "arguments" in call:
            self._ingest_arguments(state, call.get("arguments"))

        if isinstance(call.get("input"), dict) and call.get("input"):
            serialized = json.dumps(call["input"])
            self._append_tool_arguments(state, serialized)

        if call.get("status") in {"completed", "done", "finished"}:
            self._finalize_tool_state(state)

    def _ingest_arguments(self, state: ToolCallState, arguments: Any) -> None:
        if arguments is None:
            return
        if isinstance(arguments, dict):
            serialized = json.dumps(arguments)
            self._append_tool_arguments(state, serialized)
            self._finalize_tool_state(state)
            return
        if isinstance(arguments, str) and arguments:
            self._append_tool_arguments(state, arguments)

    def _append_tool_arguments(self, state: ToolCallState, text: str) -> None:
        if not text:
            return
        self._ensure_tool_created(state)
        state.argument_buffer += text
        self.events.append(
            ParserEvent(
                type="tool",
                mode="append",
                id=state.internal_id,
                is_tool_call=False,
                content=text,
            )
        )

    def _ensure_tool_created(self, state: ToolCallState) -> None:
        if state.created:
            return
        self._close_text_block()
        state.created = True
        self.events.append(
            ParserEvent(
                type="tool",
                mode="create",
                id=state.internal_id,
                is_tool_call=False,
                content=state.name or "",
            )
        )

    def _finalize_tool_state(self, state: ToolCallState) -> None:
        if state.closed:
            return
        self._ensure_tool_created(state)
        args: Dict[str, Any]
        if state.argument_buffer.strip():
            try:
                parsed = json.loads(state.argument_buffer)
            except json.JSONDecodeError:
                args = {"arguments": state.argument_buffer}
            else:
                if isinstance(parsed, dict):
                    args = parsed
                else:
                    args = {"value": parsed}
        else:
            args = {}

        self.events.append(
            ParserEvent(
                type="tool",
                mode="close",
                id=state.internal_id,
                is_tool_call=True,
                tool=ToolUse(name=state.name or "", args=args),
            )
        )
        state.closed = True
        self._remove_tool_state(state)

    def _finalize_all_tools(self) -> None:
        for state in list(self.tool_states.values()):
            self._finalize_tool_state(state)

    def _remove_tool_state(self, state: ToolCallState) -> None:
        if state.internal_id in self.tool_states:
            del self.tool_states[state.internal_id]
        for key in state.keys:
            if self.tool_lookup.get(key) == state.internal_id:
                del self.tool_lookup[key]

    def _get_or_create_tool_state(self, data: Dict[str, Any]) -> ToolCallState:
        candidates = self._collect_state_keys(data)
        state = self._find_tool_state(candidates)
        if state is None:
            internal_id = str(uuid.uuid4())
            state = ToolCallState(internal_id=internal_id)
            self.tool_states[internal_id] = state
        for key in candidates:
            if key[1] is None:
                continue
            self.tool_lookup[key] = state.internal_id
            if key not in state.keys:
                state.keys.append(key)
        return state

    def _find_tool_state(self, candidates: List[Tuple[str, Any]]) -> Optional[ToolCallState]:
        for key in candidates:
            if key[1] is None:
                continue
            internal_id = self.tool_lookup.get(key)
            if internal_id and internal_id in self.tool_states:
                return self.tool_states[internal_id]
        return None

    def _collect_state_keys(self, data: Dict[str, Any]) -> List[Tuple[str, Any]]:
        keys: List[Tuple[str, Any]] = []
        for key_name in ("tool_call_id", "id", "index", "name"):
            if key_name in data:
                keys.append((key_name, data.get(key_name)))
        function = data.get("function")
        if isinstance(function, dict):
            if "name" in function:
                keys.append(("function_name", function.get("name")))
            if "id" in function:
                keys.append(("function_id", function.get("id")))
            if "tool_call_id" in function:
                keys.append(("function_tool_call_id", function.get("tool_call_id")))
            if "index" in function:
                keys.append(("function_index", function.get("index")))
        return keys

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------
    def _stream_text(self, text: str) -> None:
        self.text_stream.stream(text)

    def _open_text_block(self) -> None:
        self.text_stream.open()

    def _close_text_block(self) -> None:
        self.text_stream.close()
