from __future__ import annotations

import html
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import guard for type hints
    from app.services.email_parser import EmailContent


_SCRIPT_STYLE_RE = re.compile(r"(?is)<(script|style).*?>.*?</\1>")
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Remove HTML/script/style tags and normalize whitespace."""
    without_script = _SCRIPT_STYLE_RE.sub(" ", text)
    without_tags = _TAG_RE.sub(" ", without_script)
    unescaped = html.unescape(without_tags)
    return _normalize_whitespace(unescaped)


def clean_body(source: str | "EmailContent") -> str:
    """Extract the text body and remove HTML. Accepts raw text or EmailContent."""
    raw = source.body if hasattr(source, "body") else str(source or "")
    return strip_html(raw)


def _normalize_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()
