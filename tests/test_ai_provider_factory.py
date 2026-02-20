import importlib.util
import sys

import pytest

from ai_writing.config_store import AIConfig, HUGGINGFACE_PROVIDER, OPENAI_PROVIDER
from ai_writing.errors import AIWritingError
from ai_writing.huggingface_client import HuggingFaceClient
from ai_writing.provider_factory import AIProviderFactory


def test_provider_factory_returns_hf_client():
    cfg = AIConfig(openai_api_key="sk", hf_api_token="hf")

    hf_client = AIProviderFactory.create(HUGGINGFACE_PROVIDER, cfg)

    assert isinstance(hf_client, HuggingFaceClient)


def test_provider_factory_returns_openai_client_when_dependency_exists(monkeypatch):
    cfg = AIConfig(openai_api_key="sk", hf_api_token="hf")

    original_find_spec = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object() if name == "openai" else original_find_spec(name))

    openai_client = AIProviderFactory.create(OPENAI_PROVIDER, cfg)

    assert openai_client.__class__.__name__ == "OpenAIClient"


def test_provider_factory_openai_missing_dependency(monkeypatch):
    cfg = AIConfig(openai_api_key="sk", hf_api_token="hf")
    monkeypatch.delitem(sys.modules, "openai", raising=False)
    original_find_spec = importlib.util.find_spec
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None if name == "openai" else original_find_spec(name))

    with pytest.raises(AIWritingError, match="instale openai para usar o provider OpenAI"):
        AIProviderFactory.create(OPENAI_PROVIDER, cfg)


def test_provider_factory_openai_does_not_depend_on_requests(monkeypatch):
    cfg = AIConfig(openai_api_key="sk", hf_api_token="hf")
    monkeypatch.delitem(sys.modules, "requests", raising=False)
    original_find_spec = importlib.util.find_spec
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name: object() if name == "openai" else original_find_spec(name),
    )

    openai_client = AIProviderFactory.create(OPENAI_PROVIDER, cfg)

    assert openai_client.__class__.__name__ == "OpenAIClient"
