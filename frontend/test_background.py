"""Keep the page background consistent before and after the app loads."""

from pathlib import Path
import re

import pytest


FRONTEND = Path(__file__).resolve().parent


@pytest.mark.parametrize("filename", ["index.html", "public/index.css"])
def test_page_background_is_original_light_slate(filename):
    source = (FRONTEND / filename).read_text()
    body_style = re.search(r"body\s*\{([^}]+)\}", source).group(1)
    assert re.search(r"background-color:\s*#f8fafc\s*;", body_style)


def test_app_shell_uses_original_light_slate_background():
    source = (FRONTEND / "App.tsx").read_text()
    shell_classes = re.search(r'<div className="(min-h-screen[^"]*)"', source).group(1)
    assert {name for name in shell_classes.split() if name.startswith("bg-")} == {
        "bg-slate-50"
    }
