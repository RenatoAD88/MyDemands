from ai_writing import key_store
from ai_writing.config_store import AIConfigStore


def test_save_and_load_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("MYDEMANDS_AI_DIR", str(tmp_path / "ai_writing"))
    monkeypatch.setattr(key_store, "AIConfigStore", AIConfigStore)

    key_store.save_api_key("  hf_123  ")

    assert key_store.load_api_key() == "hf_123"


def test_has_api_key_checks_config_file(tmp_path, monkeypatch):
    monkeypatch.setenv("MYDEMANDS_AI_DIR", str(tmp_path / "ai_writing"))
    monkeypatch.setattr(key_store, "AIConfigStore", AIConfigStore)

    assert key_store.has_api_key() is False

    key_store.save_api_key("hf-from-config")
    assert key_store.has_api_key() is True
