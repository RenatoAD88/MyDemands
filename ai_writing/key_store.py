from __future__ import annotations

from ai_writing.config_store import AIConfigStore


def load_api_key() -> str:
    return AIConfigStore().load_config().hf_api_token.strip()


def save_api_key(api_key: str) -> None:
    store = AIConfigStore()
    cfg = store.load_config()
    cfg.hf_api_token = (api_key or "").strip()
    store.save_config(cfg)


def has_api_key() -> bool:
    return bool(load_api_key())
