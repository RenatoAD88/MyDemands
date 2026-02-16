from pathlib import Path

from ai_writing import key_store


def test_save_and_load_api_key(tmp_path, monkeypatch):
    key_file = tmp_path / "ai_writing" / "chaveIA.txt"
    monkeypatch.setattr(key_store, "get_key_file_path", lambda: str(key_file))

    key_store.save_api_key("  sk-123  ")

    assert key_file.exists()
    assert key_store.load_api_key() == "sk-123"


def test_has_api_key_checks_file_and_env(tmp_path, monkeypatch):
    key_file = tmp_path / "ai_writing" / "chaveIA.txt"
    monkeypatch.setattr(key_store, "get_key_file_path", lambda: str(key_file))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    assert key_store.has_api_key() is False

    key_store.save_api_key("sk-from-file")
    assert key_store.has_api_key() is True

    key_store.save_api_key("")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
    assert key_store.has_api_key() is True
