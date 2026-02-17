from ai_writing.config_store import AIConfigStore, AIConfig, DEFAULT_PROVIDER, OPENAI_PROVIDER, HUGGINGFACE_PROVIDER


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


def test_save_config_persists_both_providers_fields(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))
    cfg = AIConfig(
        ai_enabled=True,
        ai_provider=HUGGINGFACE_PROVIDER,
        openai_api_key="sk-openai",
        hf_api_token="hf-secret",
        hf_model="HuggingFaceH4/zephyr-7b-beta",
    )
    store.save_config(cfg)

    loaded = store.load_config()
    assert loaded.ai_enabled is True
    assert loaded.ai_provider == HUGGINGFACE_PROVIDER
    assert loaded.openai_api_key == "sk-openai"
    assert loaded.hf_api_token == "hf-secret"


def test_switch_provider_does_not_erase_other_provider_config(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))
    cfg = AIConfig(openai_api_key="sk-openai", hf_api_token="hf-secret", ai_provider=OPENAI_PROVIDER)
    store.save_config(cfg)

    cfg2 = store.load_config()
    cfg2.ai_provider = HUGGINGFACE_PROVIDER
    store.save_config(cfg2)

    loaded = store.load_config()
    assert loaded.openai_api_key == "sk-openai"
    assert loaded.hf_api_token == "hf-secret"


def test_load_config_restores_provider_and_enabled_state(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))
    cfg = AIConfig(ai_enabled=True, ai_provider=HUGGINGFACE_PROVIDER)
    store.save_config(cfg)

    loaded = store.load_config()
    assert loaded.ai_enabled is True
    assert loaded.ai_provider == HUGGINGFACE_PROVIDER
