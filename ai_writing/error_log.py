from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

from ai_writing.errors import MissingAPIKeyError

from bootstrap import ensure_storage_root, resolve_storage_root


AI_ERROR_LOG_FILE_NAME = "openIA_error.log"


def ai_log_dir() -> str:
    root = resolve_storage_root()
    base_dir = ensure_storage_root(root)
    if not base_dir:
        raise OSError(f"Não foi possível criar a pasta base de armazenamento: {root}")

    path = os.path.join(base_dir, "log")
    log_dir = ensure_storage_root(path)
    if not log_dir:
        raise OSError(f"Não foi possível criar a pasta de log: {path}")

    return log_dir


def append_ai_error_log(message: str, traceback_text: str = "", context: Optional[Dict[str, Any]] = None) -> str:
    log_path = os.path.join(ai_log_dir(), AI_ERROR_LOG_FILE_NAME)
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


def log_ai_generation_error(exc: Exception, context: Optional[Dict[str, Any]] = None, traceback_text: str = "") -> str:
    message = "missing_key" if isinstance(exc, MissingAPIKeyError) else str(exc)
    return append_ai_error_log(message, traceback_text, context)
