from __future__ import annotations

import sys
import types

import pytest

from ai_writing.errors import AIRequestTimeoutError, AIWritingError, MissingAPIKeyError, ModelNotFoundError, RateLimitError
from ai_writing.huggingface_client import HuggingFaceClient


class _FakeHfHubHTTPError(Exception):
    def __init__(self, status_code: int, message: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response = types.SimpleNamespace(text=message)


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


class _FakeHfApi:
    def __init__(self):
        self.calls = []
        self.error = None

    def whoami(self, token: str):
        self.calls.append(token)
        if self.error is not None:
            raise self.error
        return {"name": "test"}


class _FakeInferenceClient:
    def __init__(self, *, api_key: str, timeout: float):
        self.api_key = api_key
        self.timeout = timeout
        self.chat = types.SimpleNamespace(completions=_FAKE_COMPLETIONS)


_FAKE_COMPLETIONS = _FakeCompletions()
_FAKE_HF_API = _FakeHfApi()


def _install_fake_hf_hub(monkeypatch, *, response_text: str = "OK", error: Exception | None = None, whoami_error: Exception | None = None):
    global _FAKE_COMPLETIONS, _FAKE_HF_API
    _FAKE_COMPLETIONS = _FakeCompletions(response_text=response_text, error=error)
    _FAKE_HF_API = _FakeHfApi()
    _FAKE_HF_API.error = whoami_error

    fake_module = types.ModuleType("huggingface_hub")
    fake_module.InferenceClient = _FakeInferenceClient
    fake_module.HfApi = lambda: _FAKE_HF_API

    fake_errors = types.ModuleType("huggingface_hub.errors")
    fake_errors.HfHubHTTPError = _FakeHfHubHTTPError

    monkeypatch.setitem(sys.modules, "huggingface_hub", fake_module)
    monkeypatch.setitem(sys.modules, "huggingface_hub.errors", fake_errors)


def test_hf_chat_completions_parsing(monkeypatch):
    _install_fake_hf_hub(monkeypatch, response_text="texto-final")
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    result = client.suggest("entrada", "instrucao", {"k": 1})

    assert result == "texto-final"
    assert _FAKE_COMPLETIONS.calls[0]["model"] == "repo/model"


def test_connectivity_validates_whoami_and_chat(monkeypatch):
    _install_fake_hf_hub(monkeypatch, response_text="OK")
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    client.check_connectivity()

    assert _FAKE_HF_API.calls == ["hf_test"]
    call = _FAKE_COMPLETIONS.calls[0]
    assert call["messages"][0]["content"] == "Responda apenas: OK"
    assert call["messages"][1]["content"] == "ping"


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
    _install_fake_hf_hub(monkeypatch, error=_FakeHfHubHTTPError(status, "erro"))
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(expected):
        client.check_connectivity()


def test_connectivity_timeout(monkeypatch):
    _install_fake_hf_hub(monkeypatch, error=TimeoutError("timeout"))
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(AIRequestTimeoutError):
        client.check_connectivity()


def test_connectivity_gated_error_message(monkeypatch):
    _install_fake_hf_hub(monkeypatch, error=_FakeHfHubHTTPError(400, "Model is gated and requires acceptance"))
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(AIWritingError, match="acesso restrito"):
        client.check_connectivity()


def test_extract_exception_metadata_uses_exception_name_when_message_is_empty():
    class _SilentError(Exception):
        def __str__(self):
            return ""

    meta = HuggingFaceClient._extract_exception_metadata(_SilentError())

    assert meta["body"] == "_SilentError"
