"""Keep the page background consistent before and after the app loads."""

from pathlib import Path
import re

import pytest


FRONTEND = Path(__file__).resolve().parent


@pytest.mark.parametrize("filename", ["index.html", "public/index.css"])
def test_page_background_is_orange_yellow(filename):
    source = (FRONTEND / filename).read_text()
    body_style = re.search(r"body\s*\{([^}]+)\}", source).group(1)
    assert re.search(r"background-color:\s*#fcd34d\s*;", body_style)


def test_app_shell_does_not_cover_page_background():
    source = (FRONTEND / "App.tsx").read_text()
    shell_classes = re.search(r'<div className="(min-h-screen[^"]*)"', source).group(1)
    assert not any(name.startswith("bg-") for name in shell_classes.split())
