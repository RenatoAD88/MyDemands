from __future__ import annotations

import io
import json
import socket
from urllib.error import HTTPError

import pytest

from ai_writing.errors import AIRequestTimeoutError, MissingAPIKeyError, ModelNotFoundError, RateLimitError
from ai_writing.huggingface_client import HuggingFaceClient


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _http_error(code: int, payload: dict | None = None, url: str = "https://api-inference.huggingface.co/models/test") -> HTTPError:
    data = json.dumps(payload or {"error": "falha"}).encode("utf-8")
    return HTTPError(url=url, code=code, msg="err", hdrs={}, fp=io.BytesIO(data))


def test_connectivity_ignores_whoami_410_and_tests_inference(monkeypatch):
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    class _FakeHfApi:
        def whoami(self, token):
            raise RuntimeError("410 Gone")

    calls = []

    def _fake_find_spec(name):
        if name == "huggingface_hub":
            return object()
        return None

    def _fake_import_module(name):
        if name == "huggingface_hub":
            return type("M", (), {"HfApi": _FakeHfApi})
        raise ImportError(name)

    def _fake_urlopen(req, timeout=None):
        calls.append(req.full_url)
        return _Response([{"generated_text": "OK"}])

    monkeypatch.setattr("ai_writing.huggingface_client.importlib.util.find_spec", _fake_find_spec)
    monkeypatch.setattr("ai_writing.huggingface_client.importlib.import_module", _fake_import_module)
    monkeypatch.setattr("ai_writing.huggingface_client.urllib.request.urlopen", _fake_urlopen)

    client.check_connectivity()

    assert len(calls) == 1
    assert calls[0].startswith("https://api-inference.huggingface.co/models/repo/model")


def test_inference_410_disables_legacy_endpoint_and_uses_router(monkeypatch):
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")
    seen = []
    payloads = []

    def _fake_urlopen(req, timeout=None):
        seen.append(req.full_url)
        payloads.append(json.loads(req.data.decode("utf-8")))
        if req.full_url.startswith("https://api-inference.huggingface.co/"):
            raise _http_error(410, {"error": "gone"}, url=req.full_url)
        return _Response([{"generated_text": "ok"}])

    monkeypatch.setattr("ai_writing.huggingface_client.urllib.request.urlopen", _fake_urlopen)

    assert client.suggest("texto", "instr", {}) == "ok"

    # second call should not use legacy endpoint anymore
    assert client.suggest("texto", "instr", {}) == "ok"

    assert seen[0].startswith("https://api-inference.huggingface.co/")
    assert seen[1].startswith("https://router.huggingface.co/hf-inference/")
    assert seen[2].startswith("https://router.huggingface.co/hf-inference/")
    assert payloads[0].get("options") == {"wait_for_model": True}


def test_connectivity_handles_401_404_429_timeout(monkeypatch):
    client = HuggingFaceClient(api_token="hf_test", model="repo/model")

    monkeypatch.setattr("ai_writing.huggingface_client.importlib.util.find_spec", lambda _name: None)

    monkeypatch.setattr(
        "ai_writing.huggingface_client.urllib.request.urlopen",
        lambda _req, timeout=None: (_ for _ in ()).throw(_http_error(401, {"error": "bad token"})),
    )
    with pytest.raises(MissingAPIKeyError, match="Token inválido"):
        client.check_connectivity()

    monkeypatch.setattr(
        "ai_writing.huggingface_client.urllib.request.urlopen",
        lambda _req, timeout=None: (_ for _ in ()).throw(_http_error(404, {"error": "model not found"})),
    )
    with pytest.raises(ModelNotFoundError, match="Modelo não encontrado"):
        client.check_connectivity()

    monkeypatch.setattr(
        "ai_writing.huggingface_client.urllib.request.urlopen",
        lambda _req, timeout=None: (_ for _ in ()).throw(_http_error(429, {"error": "too many"})),
    )
    with pytest.raises(RateLimitError, match="Rate limit"):
        client.check_connectivity()

    monkeypatch.setattr(
        "ai_writing.huggingface_client.urllib.request.urlopen",
        lambda _req, timeout=None: (_ for _ in ()).throw(socket.timeout("timeout")),
    )
    with pytest.raises(AIRequestTimeoutError, match="Timeout"):
        client.check_connectivity()
