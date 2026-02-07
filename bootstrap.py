from __future__ import annotations

import os
import sys
from typing import Optional

WINDOWS_APP_ROOT = r"C:\MyDemands"


def resolve_storage_root(executable_path: str | None = None) -> str:
    if os.name == "nt":
        return WINDOWS_APP_ROOT
    base = executable_path or sys.argv[0]
    return os.path.dirname(os.path.abspath(base))


def ensure_storage_root(storage_root: str) -> Optional[str]:
    if os.path.isdir(storage_root):
        return storage_root

    try:
        os.makedirs(storage_root, exist_ok=True)
    except OSError:
        return None

    if not os.path.isdir(storage_root):
        return None

    return storage_root
