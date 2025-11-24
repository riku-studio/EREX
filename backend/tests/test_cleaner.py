from app.services.cleaner import clean_body, strip_html
from app.services.email_parser import EmailContent


def test_strip_html_removes_tags_and_scripts():
    html_text = "<html><body><script>alert(1)</script><b>Hello</b> world</body></html>"
    assert strip_html(html_text) == "Hello world"


def test_clean_body_from_text():
    raw = "Hi<br><div>there</div>"
    assert clean_body(raw) == "Hi\nthere"


def test_clean_body_from_email_content():
    content = EmailContent(source_path="x", body="<p>Line1</p><p>Line2</p>")
    assert clean_body(content) == "Line1\nLine2"


def test_clean_body_keeps_newlines_from_text():
    raw = "a line\n  another\tline\n\nlast"
    assert clean_body(raw) == "a line\nanother line\nlast"
