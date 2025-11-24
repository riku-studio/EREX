import sys
from pathlib import Path

import pytest


# Ensure backend root is importable when tests are executed from different cwd.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture
def anyio_backend():
    # Force anyio-based tests to run on asyncio only; trio is not installed.
    return "asyncio"
