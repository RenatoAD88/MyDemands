from types import SimpleNamespace

import pytest

from ai_writing.openai_client import MissingAPIKeyError, OpenAIWritingClient


class FakeRateLimitError(Exception):
    status_code = 429


class FakeOpenAI:
    def __init__(self, *args, **kwargs):
        self.responses = SimpleNamespace(create=self._create)
        self.calls = 0
        self._mode = kwargs.get("mode", "ok")

    def _create(self, **kwargs):
        self.calls += 1
        if self._mode == "ok":
            return SimpleNamespace(output_text="Texto sugerido")
        raise FakeRateLimitError("429")


def test_suggest_returns_output_text(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    fake = FakeOpenAI()
    monkeypatch.setattr("ai_writing.openai_client.OpenAI", lambda *args, **kwargs: fake)
    client = OpenAIWritingClient()
    result = client.suggest("Texto", "Instrução", {"field": "Descrição"})
    assert result == "Texto sugerido"


def test_suggest_retries_on_429(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    calls = {"count": 0}

    class RetryOpenAI:
        def __init__(self, *args, **kwargs):
            self.responses = SimpleNamespace(create=self._create)

        def _create(self, **kwargs):
            calls["count"] += 1
            if calls["count"] < 3:
                raise FakeRateLimitError("429")
            return SimpleNamespace(output_text="ok")

    sleeps = []
    monkeypatch.setattr("ai_writing.openai_client.OpenAI", RetryOpenAI)
    monkeypatch.setattr("ai_writing.openai_client.time.sleep", lambda sec: sleeps.append(sec))

    client = OpenAIWritingClient(max_retries=5)
    assert client.suggest("Texto", "Instr", {}) == "ok"
    assert calls["count"] == 3
    assert len(sleeps) == 2


def test_missing_key_raises_specific_error(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("ai_writing.openai_client.OpenAI", lambda *args, **kwargs: FakeOpenAI())
    client = OpenAIWritingClient(api_key=None)
    with pytest.raises(MissingAPIKeyError):
        client.suggest("abc", "i", {})


def test_missing_openai_dependency_raises_specific_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("ai_writing.openai_client.OpenAI", None)

    from ai_writing.openai_client import MissingOpenAIDependencyError

    client = OpenAIWritingClient()
    with pytest.raises(MissingOpenAIDependencyError):
        client.suggest("abc", "i", {})
