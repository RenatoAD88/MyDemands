from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

from ai_writing.errors import AIRequestTimeoutError, AIWritingError
from ai_writing.huggingface_client import HF_CHAT_COMPLETIONS_URL, HuggingFaceClient


class _FakeHTTPError(Exception):
    def __init__(self, status_code: int, body: str):
        super().__init__(body)
        self.status_code = status_code
        self.response = types.SimpleNamespace(status_code=status_code, text=body)


class _FakeResponse:
    def __init__(self, payload=None, *, status_code: int = 200, body: str = ""):
        self._payload = payload if payload is not None else {"choices": [{"message": {"content": "OK"}}]}
        self.status_code = status_code
        self.text = body or json.dumps(self._payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise _FakeHTTPError(self.status_code, self.text)

    def json(self):
        return self._payload


class _FakeRequests:
    class exceptions:
        Timeout = TimeoutError

    def __init__(self):
        self.calls = []
        self.response = _FakeResponse()
        self.error = None

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        if self.error is not None:
            raise self.error
        return self.response


_FAKE_REQUESTS = _FakeRequests()


def _install_fake_requests(monkeypatch, *, payload=None, status_code: int = 200, body: str = "", error: Exception | None = None):
    global _FAKE_REQUESTS
    _FAKE_REQUESTS = _FakeRequests()
    _FAKE_REQUESTS.response = _FakeResponse(payload=payload, status_code=status_code, body=body)
    _FAKE_REQUESTS.error = error

    fake_module = types.ModuleType("requests")
    fake_module.post = _FAKE_REQUESTS.post
    fake_module.exceptions = _FakeRequests.exceptions

    monkeypatch.setitem(sys.modules, "requests", fake_module)


def test_hf_chat_completions_parsing(monkeypatch):
    _install_fake_requests(monkeypatch, payload={"choices": [{"message": {"content": "texto-final"}}]})
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    result = client.suggest("entrada", "instrucao", {"k": 1})

    assert result == "texto-final"
    assert _FAKE_REQUESTS.calls[0]["json"]["model"] == "repo/model"


def test_connectivity_uses_router_and_ping(monkeypatch):
    _install_fake_requests(monkeypatch, payload={"choices": [{"message": {"content": "OK"}}]})
    client = HuggingFaceClient(api_token="hf_test", model="repo/model", max_new_tokens=300)

    client.check_connectivity()

    call = _FAKE_REQUESTS.calls[0]
    assert call["url"] == HF_CHAT_COMPLETIONS_URL
    assert call["json"]["messages"][1]["content"] == "ping"
    assert call["json"]["max_tokens"] == 16


@pytest.mark.parametrize("status", [401, 403, 404, 429])
def test_connectivity_raises_mapped_error(monkeypatch, status):
    _install_fake_requests(monkeypatch, status_code=status, body="erro")
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(AIWritingError):
        client.check_connectivity()


def test_connectivity_timeout(monkeypatch):
    _install_fake_requests(monkeypatch, error=TimeoutError("timeout"))
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(AIRequestTimeoutError):
        client.check_connectivity()


def test_extracts_text_from_multiple_response_shapes(monkeypatch):
    _install_fake_requests(monkeypatch, payload={"choices": [{"message": {"content": "  texto-dict  "}}]})
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    assert client.suggest("entrada", "instrucao", {"field": "Descrição"}) == "texto-dict"

    _install_fake_requests(monkeypatch, payload=[{"generated_text": "lista-gerada"}])

    assert client.suggest("entrada", "instrucao", {"field": "Descrição"}) == "lista-gerada"


def test_logs_dump_and_raises_when_response_has_no_text(monkeypatch, tmp_path):
    _install_fake_requests(monkeypatch, payload={"foo": "bar", "token": "secret"})
    monkeypatch.setattr("ai_writing.error_log.resolve_storage_root", lambda: str(tmp_path))
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(AIWritingError, match="formato inesperado"):
        client.suggest("entrada", "instrucao", {"demand_id": "D-1", "field": "Descrição"})

    log_file = Path(tmp_path / "log" / "huggingFace_error.txt")
    content = log_file.read_text(encoding="utf-8")
    assert "provider" in content
    assert "demand_id" in content
    assert "response_dump" in content
    assert "secret" not in content


def test_extract_exception_metadata_uses_exception_name_when_message_is_empty():
    class _SilentError(Exception):
        def __str__(self):
            return ""

    meta = HuggingFaceClient._extract_exception_metadata(_SilentError())

    assert meta["body"] == "_SilentError"


def test_missing_requests_dependency_returns_friendly_error(monkeypatch):
    monkeypatch.delitem(sys.modules, "requests", raising=False)

    real_import = __import__

    def _fake_import(name, *args, **kwargs):
        if name == "requests":
            raise ImportError("No module named requests")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _fake_import)
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    with pytest.raises(AIWritingError, match="instale requests"):
        client.check_connectivity()


def test_huggingface_does_not_import_openai(monkeypatch):
    _install_fake_requests(monkeypatch, payload={"choices": [{"message": {"content": "OK"}}]})
    monkeypatch.delitem(sys.modules, "openai", raising=False)
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    client.check_connectivity()

    assert "openai" not in sys.modules
