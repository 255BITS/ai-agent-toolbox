"""Utility helpers shared across parser implementations."""

from __future__ import annotations


def longest_prefix_at_end(buf: str, full_str: str) -> int:
    """Return length of the longest prefix of ``full_str`` found at the end of ``buf``.

    This mirrors the prefix-preservation logic used by the streaming parsers to
    keep partial tag or fence delimiters across chunk boundaries. Only strict
    prefixes of ``full_str`` are considered (i.e. a complete match returns 0).
    """

    if not buf or not full_str:
        return 0

    max_len = min(len(buf), max(len(full_str) - 1, 0))
    for length in range(max_len, 0, -1):
        if buf.endswith(full_str[:length]):
            return length
    return 0


__all__ = ["longest_prefix_at_end"]
