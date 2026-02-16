from types import SimpleNamespace

import pytest

from ai_writing.huggingface_client import (
    AIRequestTimeoutError,
    AIWritingError,
    HuggingFaceClient,
    MissingAPIKeyError,
    ModelNotFoundError,
    RateLimitError,
)


class _HTTPError(Exception):
    def __init__(self, status_code, message="http error"):
        super().__init__(message)
        self.response = SimpleNamespace(status_code=status_code)


class _FakeInferenceClient:
    def __init__(self, api_key, timeout=None):
        self.api_key = api_key
        self.timeout = timeout
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self.calls = []
        self.behavior = None

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if callable(self.behavior):
            return self.behavior(**kwargs)
        return self.behavior


@pytest.fixture
def fake_client(monkeypatch):
    holder = {}

    def _factory(api_key, timeout=None):
        client = _FakeInferenceClient(api_key=api_key, timeout=timeout)
        holder["client"] = client
        return client

    monkeypatch.setattr("ai_writing.huggingface_client.InferenceClient", _factory)
    return holder


def _completion(content: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


def test_token_ausente():
    client = HuggingFaceClient(api_token="")
    with pytest.raises(MissingAPIKeyError):
        client.suggest("abc", "instr")


def test_suggest_parseia_completion_content(fake_client):
    client = HuggingFaceClient(api_token="hf-token", model="zai-org/GLM-5:novita")
    fake_client["client"].behavior = _completion("Texto final")

    assert client.suggest("abc", "instr") == "Texto final"


def test_modelo_invalido_404(fake_client):
    client = HuggingFaceClient(api_token="hf-token", model="invalid/model")
    fake_client["client"].behavior = lambda **kwargs: (_ for _ in ()).throw(_HTTPError(404))

    with pytest.raises(ModelNotFoundError):
        client.suggest("abc", "instr")


def test_rate_limit_tratado(fake_client):
    client = HuggingFaceClient(api_token="hf-token")
    fake_client["client"].behavior = lambda **kwargs: (_ for _ in ()).throw(_HTTPError(429))

    with pytest.raises(RateLimitError):
        client.suggest("abc", "instr")


def test_missing_api_key_401_403(fake_client):
    client = HuggingFaceClient(api_token="hf-token")
    for status in (401, 403):
        fake_client["client"].behavior = lambda **kwargs: (_ for _ in ()).throw(_HTTPError(status))
        with pytest.raises(MissingAPIKeyError):
            client.suggest("abc", "instr")


def test_timeout_tratado(fake_client):
    client = HuggingFaceClient(api_token="hf-token")
    fake_client["client"].behavior = lambda **kwargs: (_ for _ in ()).throw(TimeoutError("timed out"))

    with pytest.raises(AIRequestTimeoutError):
        client.suggest("abc", "instr")


def test_check_connectivity_faz_inferencia_minima(fake_client):
    client = HuggingFaceClient(api_token="hf-token", max_new_tokens=64)
    fake_client["client"].behavior = _completion("pong")

    assert client.check_connectivity() is None
    assert fake_client["client"].calls
    assert fake_client["client"].calls[0]["messages"] == [{"role": "user", "content": "ping"}]


def test_check_connectivity_falha_se_retorno_vazio(fake_client):
    client = HuggingFaceClient(api_token="hf-token")
    fake_client["client"].behavior = _completion("   ")

    with pytest.raises(AIWritingError, match="(resposta vazia|conteúdo textual)"):
        client.check_connectivity()
