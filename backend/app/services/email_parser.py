from __future__ import annotations

import argparse
import platform
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
    if platform.system() != "Windows":
        return [
            EmailContent(
                source_path=str(path),
                parser="pst",
                error="PST parsing requires Windows and pywin32; convert to .msg on non-Windows",
            )
        ]
    try:
        import win32com.client
        import pythoncom
    except Exception:  # pragma: no cover - optional dependency
        return [
            EmailContent(
                source_path=str(path),
                parser="pst",
                error="missing dependency: install pywin32 to parse .pst files",
            )
        ]

    # Basic traversal using Outlook COM; keep scope minimal
    pythoncom.CoInitialize()
    messages: List[EmailContent] = []
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        namespace = outlook.GetNamespace("MAPI")
        namespace.AddStore(str(path))
        stores = namespace.Stores
        pst_store = None
        for store in stores:
            if store.FilePath == str(path):
                pst_store = store
                break
        if not pst_store:
            return [
                EmailContent(
                    source_path=str(path),
                    parser="pst",
                    error="unable to open PST store via Outlook",
                )
            ]
        root_folder = pst_store.GetRootFolder()
        _collect_pst_folder(root_folder, messages)
        namespace.RemoveStore(root_folder)
    except Exception as exc:  # pragma: no cover - defensive
        messages.append(
            EmailContent(
                source_path=str(path),
                parser="pst",
                error=f"failed to parse pst: {exc}",
            )
        )
    finally:
        pythoncom.CoUninitialize()
    return messages


def _collect_pst_folder(folder, messages: List[EmailContent], folder_name: Optional[str] = None):
    try:
        folder_name = folder_name or folder.Name
        for item in folder.Items:
            try:
                if getattr(item, "Class", None) == 43:  # olMail
                    messages.append(_pst_item_to_content(item, folder_name))
            except Exception:
                continue
        for sub in folder.Folders:
            _collect_pst_folder(sub, messages, sub.Name)
    except Exception:
        return


def _pst_item_to_content(item, folder_name: str) -> EmailContent:
    content = EmailContent(source_path=folder_name, parser="pst")
    content.subject = getattr(item, "Subject", "") or ""
    sender_name = getattr(item, "SenderName", "") or ""
    sender_address = getattr(item, "SenderEmailAddress", "") or ""
    content.sender = sender_name or sender_address

    recips: List[str] = []
    for field, prefix in (("To", ""), ("CC", "CC: "), ("BCC", "BCC: ")):
        try:
            value = getattr(item, field, None)
            if value:
                recips.append(f"{prefix}{value}")
        except Exception:
            continue
    content.recipients = recips

    received = getattr(item, "ReceivedTime", None)
    if isinstance(received, datetime):
        content.received_at = received.strftime("%Y-%m-%d %H:%M:%S")
    elif received:
        content.received_at = str(received)

    created = getattr(item, "CreationTime", None)
    if isinstance(created, datetime):
        content.created_at = created.strftime("%Y-%m-%d %H:%M:%S")
    elif created:
        content.created_at = str(created)

    content.body = getattr(item, "Body", "") or ""
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
