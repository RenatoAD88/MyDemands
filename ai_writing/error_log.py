from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

from bootstrap import resolve_storage_root


def ai_log_dir() -> str:
    root = resolve_storage_root()
    path = os.path.join(root, "log")
    os.makedirs(path, exist_ok=True)
    return path


def append_ai_error_log(message: str, traceback_text: str = "", context: Optional[Dict[str, Any]] = None) -> str:
    log_path = os.path.join(ai_log_dir(), "ai_errors.log")
    when = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context_repr = context or {}
    body = [
        f"[{when}] {message}",
        f"context={context_repr}",
    ]
    if traceback_text:
        body.append(traceback_text.rstrip())
    body.append("-" * 80)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")
    return log_path
