from __future__ import annotations

import re
from typing import Iterable, List

from app.utils.config import Config

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_URL_RE = re.compile(r"(https?://|www\.)|\bURL\s*:", re.IGNORECASE)
_PHONE_RE = re.compile(r"\d{2,4}-\d{2,4}-\d{3,4}")
_PUNCT_DIGIT_RE = re.compile(r"^[\d\W_]+$")


class LineFilter:
    """Config-driven lightweight line filter between cleaner and semantic."""

    def __init__(self, config: type[Config] = Config):
        self.config = config
        self.enabled = getattr(config, "ENABLE_LINE_FILTER", True)
        self.decoration_chars = set(config.LINE_FILTER_DECORATION_CHARS)
        self.job_keywords = list(config.LINE_FILTER_JOB_KEYWORDS)
        self.signature_keywords = list(config.LINE_FILTER_SIGNATURE_KEYWORDS)
        self.company_prefixes = tuple(config.LINE_FILTER_SIGNATURE_COMPANY_PREFIX)
        self.force_delete_patterns = self._compile_patterns(getattr(config, "LINE_FILTER_FORCE_DELETE_PATTERNS", []))
        self.greeting_patterns = self._compile_patterns(config.LINE_FILTER_GREETING_PATTERNS)
        self.closing_patterns = self._compile_patterns(config.LINE_FILTER_CLOSING_PATTERNS)
        self.footer_patterns = self._compile_patterns(config.LINE_FILTER_FOOTER_PATTERNS)

    def filter_lines(self, lines: List[str]) -> List[str]:
        """Return lines after negative filtering; preserves job-related lines."""
        if not self.enabled:
            return list(lines)

        kept: List[str] = []
        for line in lines:
            if self._matches_any(self.force_delete_patterns, line):
                continue
            if self._contains_job_keyword(line):
                kept.append(line)
                continue
            if self._is_garbage_line(line):
                continue
            kept.append(line)
        return kept

    def _contains_job_keyword(self, line: str) -> bool:
        return any(keyword in line for keyword in self.job_keywords)

    def _is_garbage_line(self, line: str) -> bool:
        trimmed = line.strip()
        if not trimmed:
            return True
        if self._is_decorative(trimmed):
            return True
        if self._is_short_noise(trimmed):
            return True
        if self._matches_any(self.greeting_patterns, trimmed):
            return True
        if self._matches_any(self.closing_patterns, trimmed):
            return True
        if self._looks_like_signature(trimmed):
            return True
        if self._matches_any(self.footer_patterns, trimmed):
            return True
        return False

    def _is_decorative(self, line: str) -> bool:
        compact = re.sub(r"\s+", "", line)
        if compact and all(ch in self.decoration_chars for ch in compact):
            return True
        if len(compact) >= 3 and not compact[0].isalnum() and all(ch == compact[0] for ch in compact):
            return True
        return False

    @staticmethod
    def _compile_patterns(patterns: Iterable[str]) -> List[re.Pattern[str]]:
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    @staticmethod
    def _matches_any(patterns: Iterable[re.Pattern[str]], line: str) -> bool:
        return any(p.search(line) for p in patterns)

    @staticmethod
    def _is_short_noise(line: str) -> bool:
        return len(line) <= 4 and bool(_PUNCT_DIGIT_RE.match(line))

    def _looks_like_signature(self, line: str) -> bool:
        if _EMAIL_RE.search(line):
            return True
        if _URL_RE.search(line):
            return True
        if _PHONE_RE.search(line):
            return True
        if any(keyword in line for keyword in self.signature_keywords):
            return True
        if self.company_prefixes and line.startswith(self.company_prefixes):
            return True
        return False
