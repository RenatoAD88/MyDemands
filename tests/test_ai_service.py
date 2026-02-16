from datetime import date, timedelta

import pytest

from ai_writing.config_store import AIConfig, AIConfigStore, OPENAI_PROVIDER
from ai_writing.errors import UsageLimitReachedError
from ai_writing.service import AIWritingService


class FakeClient:
    calls = 0

    def __init__(self, **kwargs):
        pass

    def build_prompt(self, input_text, instruction, context):
        return f"{instruction}|{input_text}|{context}"

    def suggest(self, input_text, instruction, context):
        FakeClient.calls += 1
        return f"resp-{FakeClient.calls}"


def _seed_config(store: AIConfigStore, **kwargs):
    cfg = AIConfig(openai_api_key="sk-token")
    for key, value in kwargs.items():
        setattr(cfg, key, value)
    store.save_config(cfg, provider=OPENAI_PROVIDER)


def test_incremento_correto_do_contador(tmp_path, monkeypatch):
    store = AIConfigStore(str(tmp_path / "ai"))
    _seed_config(store, ia_usage_count=0, ia_usage_limit=200)
    service = AIWritingService(store)
    monkeypatch.setattr(service, "_resolve_client", lambda provider: FakeClient)

    service.generate("txt", "instr", {}, provider=OPENAI_PROVIDER)

    assert store.load_config(provider=OPENAI_PROVIDER).ia_usage_count == 1


def test_bloqueio_ao_atingir_limite(tmp_path, monkeypatch):
    store = AIConfigStore(str(tmp_path / "ai"))
    _seed_config(store, ia_usage_count=3, ia_usage_limit=3, ia_last_reset=date.today().strftime("%Y-%m-%d"))
    service = AIWritingService(store)
    monkeypatch.setattr(service, "_resolve_client", lambda provider: FakeClient)

    with pytest.raises(UsageLimitReachedError):
        service.generate("txt", "instr", {}, provider=OPENAI_PROVIDER)


def test_reset_automatico(tmp_path, monkeypatch):
    store = AIConfigStore(str(tmp_path / "ai"))
    reset_date = (date.today() - timedelta(days=31)).strftime("%Y-%m-%d")
    _seed_config(store, ia_usage_count=10, ia_usage_limit=200, ia_last_reset=reset_date)
    service = AIWritingService(store)
    monkeypatch.setattr(service, "_resolve_client", lambda provider: FakeClient)

    service.generate("txt", "instr", {}, provider=OPENAI_PROVIDER)

    cfg = store.load_config(provider=OPENAI_PROVIDER)
    assert cfg.ia_usage_count == 1
    assert cfg.ia_last_reset == date.today().strftime("%Y-%m-%d")


def test_cache_evita_nova_chamada(tmp_path, monkeypatch):
    FakeClient.calls = 0
    store = AIConfigStore(str(tmp_path / "ai"))
    _seed_config(store, ia_usage_count=0, ia_usage_limit=200, ia_cache_enabled=True)
    service = AIWritingService(store)
    monkeypatch.setattr(service, "_resolve_client", lambda provider: FakeClient)

    first = service.generate("txt", "instr", {"k": 1}, provider=OPENAI_PROVIDER)
    second = service.generate("txt", "instr", {"k": 1}, provider=OPENAI_PROVIDER)

    assert first == second
    assert FakeClient.calls == 1
    assert store.load_config(provider=OPENAI_PROVIDER).ia_usage_count == 1


def test_remocao_cache_antigo_ao_ultrapassar_1000(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))
    for idx in range(1002):
        store.save_cache_response(f"key-{idx}", f"value-{idx}", provider=OPENAI_PROVIDER)

    cache = store.load_cache(provider=OPENAI_PROVIDER)
    assert len(cache) == 1000
    assert "key-0" not in cache
    assert "key-1" not in cache
