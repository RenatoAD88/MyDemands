from __future__ import annotations

import os

KEY_FILE_NAME = "chaveIA.txt"


def get_key_file_path() -> str:
    return os.path.join(os.path.dirname(__file__), KEY_FILE_NAME)


def load_api_key() -> str:
    path = get_key_file_path()
    try:
        with open(path, "r", encoding="utf-8") as fp:
            return fp.read().strip()
    except OSError:
        return ""


def save_api_key(api_key: str) -> None:
    path = get_key_file_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        fp.write((api_key or "").strip())


def has_api_key() -> bool:
    return bool(load_api_key() or os.getenv("OPENAI_API_KEY", "").strip())
