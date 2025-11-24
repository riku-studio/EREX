from email.message import EmailMessage
from pathlib import Path

from app.services.email_parser import parse_directory, parse_email_file


def _write_eml(tmp_path: Path, name: str, *, html: bool = False) -> Path:
    msg = EmailMessage()
    msg["Subject"] = "Test Subject"
    msg["From"] = "sender@example.com"
    msg["To"] = "user@example.com"
    if html:
        msg.set_content("<b>Hello</b>", subtype="html")
    else:
        msg.set_content("Hello plain")

    target = tmp_path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(msg.as_bytes())
    return target


def test_parse_email_file_eml_plain(tmp_path: Path):
    eml_path = _write_eml(tmp_path, "sample.eml")
    results = parse_email_file(eml_path)

    assert len(results) == 1
    item = results[0]
    assert item.parser == "eml"
    assert item.subject == "Test Subject"
    assert item.sender == "sender@example.com"
    assert "user@example.com" in item.recipients
    assert item.body.strip() == "Hello plain"


def test_parse_email_file_eml_html(tmp_path: Path):
    eml_path = _write_eml(tmp_path, "sample_html.eml", html=True)
    results = parse_email_file(eml_path)

    assert len(results) == 1
    item = results[0]
    assert item.body.strip() == "Hello"


def test_parse_directory_includes_eml(tmp_path: Path):
    _write_eml(tmp_path, "nested/sample.EML")

    results = parse_directory(tmp_path)
    names = [Path(r.source_path).name for r in results]

    assert "sample.EML" in names
