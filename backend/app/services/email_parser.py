from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.utils.logging import logger


@dataclass
class EmailContent:
    source_path: str
    subject: str = ""
    sender: str = ""
    recipients: List[str] = field(default_factory=list)
    received_at: Optional[str] = None
    created_at: Optional[str] = None
    body: str = ""
    parser: str = ""
    error: Optional[str] = None


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def _parse_msg(path: Path) -> EmailContent:
    content = EmailContent(source_path=str(path))
    try:
        import extract_msg
    except Exception:  # pragma: no cover - optional dependency
        content.error = "missing dependency: install extract-msg to parse .msg files"
        return content

    try:
        msg = extract_msg.Message(str(path))
        content.subject = msg.subject or ""
        content.sender = msg.sender or getattr(msg, "senderEmail", "") or ""

        recips: List[str] = []
        for field in ("to", "cc", "bcc"):
            value = getattr(msg, field, None)
            if value:
                prefix = "" if field == "to" else f"{field.upper()}: "
                parts = [part.strip() for part in value.split(";") if part.strip()]
                recips.extend([f"{prefix}{p}" for p in parts])
        content.recipients = recips

        # Dates
        raw_date = getattr(msg, "date", None)
        if isinstance(raw_date, datetime):
            content.received_at = raw_date.strftime("%Y-%m-%d %H:%M:%S")
        elif raw_date:
            content.received_at = str(raw_date)

        html_body = getattr(msg, "htmlBody", None)
        body = msg.body or ""
        if not body and html_body:
            body = _strip_html(html_body)
        content.body = body
        content.parser = "extract-msg"
    except Exception as exc:  # pragma: no cover - defensive
        content.error = f"failed to parse msg: {exc}"
    finally:
        try:
            msg.close()
        except Exception:
            pass
    return content


def _parse_pst(path: Path) -> List[EmailContent]:
    try:
        import pypff  # type: ignore
    except Exception:
        return [
            EmailContent(
                source_path=str(path),
                parser="pst",
                error="missing dependency: install pypff (libpff) to parse .pst files on Linux",
            )
        ]

    messages: List[EmailContent] = []
    try:
        pst = pypff.file()
        pst.open(str(path))
        root = pst.get_root_folder()
        _collect_pst_folder(root, messages)
    except Exception as exc:  # pragma: no cover - defensive
        messages.append(
            EmailContent(
                source_path=str(path),
                parser="pst",
                error=f"failed to parse pst: {exc}",
            )
        )
    finally:
        try:
            pst.close()  # type: ignore
        except Exception:
            pass
    return messages


def _collect_pst_folder(folder, messages: List[EmailContent], folder_name: Optional[str] = None):
    folder_name = folder_name or getattr(folder, "get_name", lambda: "Root")()
    try:
        for i in range(folder.get_number_of_sub_messages()):
            try:
                item = folder.get_sub_message(i)
                messages.append(_pst_item_to_content(item, folder_name))
            except Exception:
                continue
        for i in range(folder.get_number_of_sub_folders()):
            try:
                sub = folder.get_sub_folder(i)
                _collect_pst_folder(sub, messages, sub.get_name())
            except Exception:
                continue
    except Exception:
        return


def _pst_item_to_content(item, folder_name: str) -> EmailContent:
    content = EmailContent(source_path=folder_name, parser="pypff")
    content.subject = getattr(item, "get_subject", lambda: "")() or ""
    sender_name = getattr(item, "get_sender_name", lambda: "")() or ""
    sender_address = getattr(item, "get_sender_email_address", lambda: "")() or ""
    content.sender = sender_name or sender_address

    recips: List[str] = []
    try:
        for i in range(item.get_number_of_recipients()):
            r = item.get_recipient(i)
            name = getattr(r, "get_name", lambda: "")() or ""
            email = getattr(r, "get_email_address", lambda: "")() or ""
            recips.append(name or email)
    except Exception:
        pass
    content.recipients = recips

    received = getattr(item, "get_delivery_time", lambda: None)()
    if isinstance(received, datetime):
        content.received_at = received.strftime("%Y-%m-%d %H:%M:%S")
    elif received:
        content.received_at = str(received)

    created = getattr(item, "get_creation_time", lambda: None)()
    if isinstance(created, datetime):
        content.created_at = created.strftime("%Y-%m-%d %H:%M:%S")
    elif created:
        content.created_at = str(created)

    body = getattr(item, "get_plain_text_body", lambda: "")() or ""
    if not body:
        body = getattr(item, "get_html_body", lambda: "")() or ""
    content.body = body
    return content


def parse_email_file(path: Path) -> List[EmailContent]:
    path = path.resolve()
    suffix = path.suffix.lower()
    if suffix == ".msg":
        return [_parse_msg(path)]
    if suffix == ".pst":
        return _parse_pst(path)
    raise ValueError(f"unsupported file type: {suffix}")


def parse_directory(path: Path) -> List[EmailContent]:
    messages: List[EmailContent] = []
    for msg_file in path.rglob("*.msg"):
        messages.extend(parse_email_file(msg_file))
    for msg_file in path.rglob("*.MSG"):
        messages.extend(parse_email_file(msg_file))
    for pst_file in path.rglob("*.pst"):
        messages.extend(parse_email_file(pst_file))
    for pst_file in path.rglob("*.PST"):
        messages.extend(parse_email_file(pst_file))
    return messages


def main():
    parser = argparse.ArgumentParser(description="Parse MSG/PST files into structured summaries.")
    parser.add_argument("input", help="Path to a .msg/.pst file or a directory to scan")
    args = parser.parse_args()

    target = Path(args.input)
    if not target.exists():
        raise SystemExit(f"input path does not exist: {target}")

    if target.is_file():
        results = parse_email_file(target)
    else:
        results = parse_directory(target)

    for item in results:
        logger.info(
            {
                "source": item.source_path,
                "subject": item.subject,
                "sender": item.sender,
                "received_at": item.received_at,
                "parser": item.parser or "n/a",
                "error": item.error,
                "body_preview": (item.body or "").strip()[:120],
            }
        )


if __name__ == "__main__":
    main()
