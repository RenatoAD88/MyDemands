from ai_writing.config_store import AIConfigStore, AIConfig, DEFAULT_PROVIDER, OPENAI_PROVIDER


def test_config_openai_is_persisted(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))

    cfg = AIConfig(openai_api_key="sk-1", openai_model="gpt-4o-mini")
    store.save_config(cfg, provider=OPENAI_PROVIDER)

    loaded = store.load_config(provider=OPENAI_PROVIDER)
    assert loaded.openai_api_key == "sk-1"
    assert loaded.openai_model == "gpt-4o-mini"


def test_cache_is_saved_for_openai(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))

    store.save_cache_response("key", "openai-response", provider=OPENAI_PROVIDER)

    assert store.get_cached_response("key", provider=OPENAI_PROVIDER) == "openai-response"


def test_default_provider_is_openai():
    assert DEFAULT_PROVIDER == OPENAI_PROVIDER
