from __future__ import annotations

import importlib.util
import sys
import types

import pytest

from ai_writing.errors import AIRequestTimeoutError, AIWritingError, MissingAPIKeyError, ModelNotFoundError, RateLimitError
from ai_writing.huggingface_client import HF_ROUTER_BASE_URL, HuggingFaceClient


class _FakeOpenAIError(Exception):
    def __init__(self, status_code: int | None = None, message: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response = types.SimpleNamespace(status_code=status_code, text=message)


class _FakeCompletions:
    def __init__(self, response_text: str = "OK", error: Exception | None = None):
        self.response_text = response_text
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=self.response_text))]
        )


class _FakeOpenAIClient:
    def __init__(self, *, base_url: str, api_key: str, timeout: float):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.chat = types.SimpleNamespace(completions=_FAKE_COMPLETIONS)


_FAKE_COMPLETIONS = _FakeCompletions()


def _install_fake_openai(monkeypatch, *, response_text: str = "OK", error: Exception | None = None):
    global _FAKE_COMPLETIONS
    _FAKE_COMPLETIONS = _FakeCompletions(response_text=response_text, error=error)

    fake_module = types.ModuleType("openai")
    fake_module.OpenAI = _FakeOpenAIClient
    fake_module.__spec__ = types.SimpleNamespace()

    monkeypatch.setitem(sys.modules, "openai", fake_module)
    original_find_spec = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object() if name == "openai" else original_find_spec(name))


def test_hf_chat_completions_parsing(monkeypatch):
    _install_fake_openai(monkeypatch, response_text="texto-final")
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    result = client.suggest("entrada", "instrucao", {"k": 1})

    assert result == "texto-final"
    assert _FAKE_COMPLETIONS.calls[0]["model"] == "repo/model"


def test_connectivity_uses_router_and_ping(monkeypatch):
    _install_fake_openai(monkeypatch, response_text="OK")
    client = HuggingFaceClient(api_token="hf_test", model="repo/model", max_new_tokens=300)

    client.check_connectivity()

    call = _FAKE_COMPLETIONS.calls[0]
    assert call["messages"][1]["content"] == "ping"
    assert call["max_tokens"] == 16


def test_client_initializes_with_router_url(monkeypatch):
    _install_fake_openai(monkeypatch, response_text="ok")
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    client.suggest("entrada", "instrucao", {})

    assert client._create_router_client().base_url == HF_ROUTER_BASE_URL


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, MissingAPIKeyError),
        (403, MissingAPIKeyError),
        (404, ModelNotFoundError),
        (429, RateLimitError),
    ],
)
def test_connectivity_maps_http_errors(monkeypatch, status, expected):
    _install_fake_openai(monkeypatch, error=_FakeOpenAIError(status, "erro"))
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(expected):
        client.check_connectivity()


def test_connectivity_timeout(monkeypatch):
    _install_fake_openai(monkeypatch, error=TimeoutError("timeout"))
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(AIRequestTimeoutError):
        client.check_connectivity()


def test_connectivity_provider_not_supported_maps_model_error(monkeypatch):
    _install_fake_openai(monkeypatch, error=_FakeOpenAIError(400, "not supported by any provider"))
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(ModelNotFoundError):
        client.check_connectivity()


def test_extract_exception_metadata_uses_exception_name_when_message_is_empty():
    class _SilentError(Exception):
        def __str__(self):
            return ""

    meta = HuggingFaceClient._extract_exception_metadata(_SilentError())

    assert meta["body"] == "_SilentError"


def test_missing_openai_dependency_returns_friendly_error(monkeypatch):
    monkeypatch.delitem(sys.modules, "openai", raising=False)
    monkeypatch.setattr("importlib.util.find_spec", lambda _: None)
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(AIWritingError, match="instale openai"):
        client.check_connectivity()
