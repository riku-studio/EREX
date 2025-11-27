from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Sequence

from app.utils.config import Config


@dataclass
class SplitBlock:
    text: str
    start_line: int
    end_line: int


class Splitter:
    """Identify multiple recruitment blocks based on marker lines."""

    def __init__(self, config: type[Config] = Config):
        self.config = config
        self.skip_lines = config.SPLITTER_SKIP_LINES
        self.marker_patterns = [re.compile(p) for p in config.SPLITTER_MARKER_PATTERNS]

    def _is_marker(self, line: str, index: int, total: int) -> bool:
        if index <= self.skip_lines or index >= total - self.skip_lines:
            return False
        return any(pattern.match(line) for pattern in self.marker_patterns)

    def split(self, body: str) -> List[SplitBlock]:
        lines = body.splitlines()
        total = len(lines)
        markers = [idx for idx, line in enumerate(lines) if self._is_marker(line, idx, total)]
        if not markers:
            cleaned = body.strip()
            return [SplitBlock(text=cleaned, start_line=0, end_line=total - 1)] if cleaned else []

        markers.sort()
        blocks: List[SplitBlock] = []
        for i, marker_idx in enumerate(markers):
            start = marker_idx
            end = markers[i + 1] if i + 1 < len(markers) else total
            block_lines = lines[start:end]
            text = "\n".join(block_lines).strip()
            if text:
                blocks.append(SplitBlock(text=text, start_line=start, end_line=end - 1))
        return blocks
