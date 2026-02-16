import json
import urllib.error

import pytest

from ai_writing.huggingface_client import (
    HuggingFaceClient,
    MissingAPIKeyError,
    ModelNotFoundError,
    RateLimitError,
)


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_token_ausente():
    client = HuggingFaceClient(api_token="")
    with pytest.raises(MissingAPIKeyError):
        client.suggest("abc", "instr")


def test_modelo_invalido(monkeypatch):
    def _raise(*args, **kwargs):
        raise urllib.error.HTTPError("", 404, "", None, None)

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    client = HuggingFaceClient(api_token="hf-token", model="invalid/model")
    with pytest.raises(ModelNotFoundError):
        client.suggest("abc", "instr")


def test_sucesso_geracao(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: _Response([{"generated_text": "Texto final"}]))
    client = HuggingFaceClient(api_token="hf-token")
    assert client.suggest("abc", "instr") == "Texto final"


def test_rate_limit_tratado(monkeypatch):
    def _raise(*args, **kwargs):
        raise urllib.error.HTTPError("", 429, "", None, None)

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    client = HuggingFaceClient(api_token="hf-token")
    with pytest.raises(RateLimitError):
        client.suggest("abc", "instr")
