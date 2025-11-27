from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from app.utils.config import Config


@dataclass
class ClassifierConfig:
    classes: Dict[str, List[str]]
    dedupe: bool = True
    strategy: str = "line-level-direct-match"

    @classmethod
    def from_path(cls, path: str) -> "ClassifierConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            classes=data.get("classes", {}),
            dedupe=bool(data.get("dedupe", True)),
            strategy=str(data.get("strategy", "line-level-direct-match")),
        )


class Classifier:
    """Generic regex-based classifier for job blocks."""

    def __init__(self, config_path: str, config: type[Config] = Config):
        self.config_path = config_path
        self.config = config
        self._raw = ClassifierConfig.from_path(config_path)
        self.dedupe = self._raw.dedupe
        self.strategy = self._raw.strategy
        self.patterns = self._compile_patterns(self._raw.classes)

    @staticmethod
    def _compile_patterns(class_map: Dict[str, List[str]]) -> Dict[str, List[re.Pattern[str]]]:
        compiled: Dict[str, List[re.Pattern[str]]] = {}
        for cls, patterns in class_map.items():
            compiled[cls] = [re.compile(re.escape(p)) for p in patterns]
        return compiled

    def classify_block(self, text: str) -> List[str]:
        lines = text.splitlines()
        hits: List[str] = []
        for cls, patterns in self.patterns.items():
            matched = False
            for line in lines:
                for pattern in patterns:
                    if pattern.search(line):
                        hits.append(cls)
                        matched = True
                        break
                if matched and self.dedupe:
                    break
        return hits

    def classify_blocks(self, blocks: Sequence[str]) -> Counter:
        counter: Counter = Counter()
        for block in blocks:
            classes = self.classify_block(block)
            counter.update(set(classes) if self.dedupe else classes)
        return counter

    def summarize(self, blocks: Sequence[str]) -> Dict[str, Dict[str, float]]:
        total = len(blocks)
        if total == 0:
            return {}
        counts = self.classify_blocks(blocks)
        summary: Dict[str, Dict[str, float]] = {}
        for cls, count in counts.items():
            summary[cls] = {"count": count, "ratio": count / total}
        return summary
