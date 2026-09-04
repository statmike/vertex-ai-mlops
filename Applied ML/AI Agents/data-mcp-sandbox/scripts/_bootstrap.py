"""Put `src/` on the import path so scripts can import flat modules by name.

`pyproject.toml` already does this for pytest via `pythonpath`. Scripts run
outside pytest, so they need the same one-line arrangement. Import this first.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
