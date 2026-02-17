from ai_writing.config_store import AIConfigStore


def test_hf_timeout_roundtrip(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))
    cfg = store.load_config()
    cfg.hf_timeout = 41.0
    store.save_config(cfg)

    loaded = store.load_config()
    assert loaded.hf_timeout == 41.0
