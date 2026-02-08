from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Sequence, Set

from app.utils.config import Config


def _sorted_keywords(groups: Dict[str, List[str]]) -> List[str]:
    seen: Set[str] = set()
    keywords: List[str] = []
    for values in groups.values():
        for kw in values:
            if kw not in seen:
                seen.add(kw)
                keywords.append(kw)
    return sorted(keywords, key=len, reverse=True)


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def _build_pattern(keyword: str) -> re.Pattern[str]:
    escaped = re.escape(keyword)
    # Use ASCII word boundaries so terms like `C` can match `C言語` while still
    # avoiding matches inside `COBOL` / `ABC`.
    return re.compile(rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])", re.IGNORECASE)


@dataclass
class KeywordMatch:
    keyword: str
    category: str


class KeywordExtractor:
    """Extract technical keywords per job block, counting once per block."""

    def __init__(self, config: type[Config] = Config):
        self.config = config
        self.keywords_by_category = config.keywords_tech()
        self.sorted_keywords = _sorted_keywords(self.keywords_by_category)
        self.normalized_keywords = {kw: _normalize_text(kw) for kw in self.sorted_keywords}
        self.patterns = {kw: _build_pattern(self.normalized_keywords[kw]) for kw in self.sorted_keywords}
        self.keyword_to_category = self._build_keyword_category_map()

    def _build_keyword_category_map(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for category, kws in self.keywords_by_category.items():
            for kw in kws:
                mapping[_normalize_text(kw).lower()] = category
        return mapping

    def extract_keywords(self, text: str) -> List[KeywordMatch]:
        hits: List[KeywordMatch] = []
        matched_spans: List[tuple[int, int]] = []
        normalized_text = _normalize_text(text)

        for keyword in self.sorted_keywords:
            pattern = self.patterns[keyword]
            for match in pattern.finditer(normalized_text):
                span = match.span()
                if self._overlaps(span, matched_spans):
                    continue
                matched_spans.append(span)
                category = self.keyword_to_category.get(self.normalized_keywords[keyword].lower(), "unknown")
                hits.append(KeywordMatch(keyword=keyword, category=category))
                break  # count once per block for this keyword
        return hits

    @staticmethod
    def _overlaps(span: tuple[int, int], spans: List[tuple[int, int]]) -> bool:
        return any(not (span[1] <= s[0] or span[0] >= s[1]) for s in spans)

    def count_by_keyword(self, blocks: Sequence[str]) -> Counter:
        counter: Counter = Counter()
        for block in blocks:
            matched = self.extract_keywords(block)
            unique = {m.keyword for m in matched}
            counter.update(unique)
        return counter

    def count_by_category(self, blocks: Sequence[str]) -> Dict[str, Counter]:
        categories: Dict[str, Counter] = {}
        for block in blocks:
            matched = self.extract_keywords(block)
            unique = {m.keyword for m in matched}
            for keyword in unique:
                category = self.keyword_to_category.get(keyword.lower(), "unknown")
                categories.setdefault(category, Counter())[keyword] += 1
        return categories

    def summarize(self, blocks: Sequence[str]) -> Dict[str, List[Dict[str, float]]]:
        total_blocks = len(blocks)
        if total_blocks == 0:
            return {}

        summary: Dict[str, List[Dict[str, float]]] = {}
        category_counts = self.count_by_category(blocks)
        for category, counter in category_counts.items():
            items: List[Dict[str, float]] = []
            for keyword, count in counter.most_common():
                ratio = count / total_blocks
                items.append({"keyword": keyword, "count": count, "ratio": ratio})
            summary[category] = items
        return summary
