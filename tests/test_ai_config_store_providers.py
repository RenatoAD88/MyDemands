from ai_writing.config_store import AIConfigStore, AIConfig, HF_PROVIDER, OPENAI_PROVIDER


def test_config_files_are_separated_by_provider(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))

    hf_cfg = AIConfig(hf_api_token="hf-1", hf_model="google/flan-t5-base")
    oa_cfg = AIConfig(openai_api_key="sk-1", openai_model="gpt-4o-mini")

    store.save_config(hf_cfg, provider=HF_PROVIDER)
    store.save_config(oa_cfg, provider=OPENAI_PROVIDER)

    assert store.load_config(provider=HF_PROVIDER).hf_api_token == "hf-1"
    assert store.load_config(provider=OPENAI_PROVIDER).openai_api_key == "sk-1"


def test_cache_isolated_by_provider(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))

    store.save_cache_response("key", "hf-response", provider=HF_PROVIDER)
    store.save_cache_response("key", "openai-response", provider=OPENAI_PROVIDER)

    assert store.get_cached_response("key", provider=HF_PROVIDER) == "hf-response"
    assert store.get_cached_response("key", provider=OPENAI_PROVIDER) == "openai-response"


def test_default_provider_is_openai():
    from ai_writing.config_store import DEFAULT_PROVIDER

    assert DEFAULT_PROVIDER == OPENAI_PROVIDER
