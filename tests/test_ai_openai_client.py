from __future__ import annotations

import io
import json
from urllib.error import HTTPError

import pytest

from ai_writing.errors import RateLimitError
from ai_writing.openai_client import OpenAIClient


class _Response:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _http_429(payload: dict, retry_after: str | None = None) -> HTTPError:
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    return HTTPError(
        url="https://api.openai.com/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs=headers,
        fp=io.BytesIO(json.dumps(payload).encode("utf-8")),
    )


def test_openai_client_maps_insufficient_quota_message(monkeypatch):
    client = OpenAIClient(api_key="sk-test")

    def _fake_urlopen(_req, timeout=None):
        raise _http_429({"error": {"code": "insufficient_quota", "message": "You exceeded your current quota."}})

    monkeypatch.setattr("ai_writing.openai_client.urllib.request.urlopen", _fake_urlopen)

    with pytest.raises(RateLimitError) as exc_info:
        client.suggest("texto", "instrucao", {})

    assert str(exc_info.value) == "Cota da OpenAI esgotada. Verifique faturamento e limites da conta."


def test_openai_client_retries_once_on_429_with_retry_after(monkeypatch):
    client = OpenAIClient(api_key="sk-test")
    calls = {"count": 0}
    slept = {"seconds": 0.0}

    def _fake_urlopen(_req, timeout=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise _http_429({"error": {"code": "rate_limit_exceeded", "message": "slow down"}}, retry_after="0.01")
        return _Response({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("ai_writing.openai_client.urllib.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("ai_writing.openai_client.time.sleep", lambda value: slept.__setitem__("seconds", value))

    assert client.suggest("texto", "instrucao", {}) == "ok"
    assert calls["count"] == 2
    assert slept["seconds"] == 0.01
