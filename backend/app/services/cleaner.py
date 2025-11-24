from __future__ import annotations

import html
import re
from typing import TYPE_CHECKING

from app.utils.logging import logger

if TYPE_CHECKING:  # pragma: no cover - import guard for type hints
    from app.services.email_parser import EmailContent


_SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style).*?>.*?</\1>")
_BR_RE = re.compile(r"(?is)<br\s*/?>")
_BLOCK_END_RE = re.compile(r"(?is)</(p|div|section|article|li|tr|td|th|h[1-6])>")
_TAG_RE = re.compile(r"<[^>]+>")
_INLINE_SPACE_RE = re.compile(r"[ \t\f\v]+")


def strip_html(text: str) -> str:
    """Remove HTML/script/style tags and normalize whitespace."""
    without_script = _SCRIPT_STYLE_RE.sub(" ", text)
    with_breaks = _BR_RE.sub("\n", without_script)
    with_blocks = _BLOCK_END_RE.sub("\n", with_breaks)
    without_tags = _TAG_RE.sub(" ", with_blocks)
    unescaped = html.unescape(without_tags)
    return _normalize_whitespace(unescaped)


def clean_body(source: str | "EmailContent") -> str:
    """Extract the text body and remove HTML. Accepts raw text or EmailContent."""
    raw = source.body if hasattr(source, "body") else str(source or "")
    cleaned = strip_html(raw)
    logger.info("Cleaned body: input_len=%d, output_len=%d", len(raw), len(cleaned))
    return cleaned


def _normalize_whitespace(text: str) -> str:
    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in normalized_newlines.split("\n"):
        cleaned = _INLINE_SPACE_RE.sub(" ", line).strip()
        if cleaned:  # 删除空行
            lines.append(cleaned)
    return "\n".join(lines)
