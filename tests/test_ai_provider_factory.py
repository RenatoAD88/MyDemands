from ai_writing.config_store import AIConfig, HUGGINGFACE_PROVIDER, OPENAI_PROVIDER
from ai_writing.huggingface_client import HuggingFaceClient
from ai_writing.openai_client import OpenAIClient
from ai_writing.provider_factory import AIProviderFactory


def test_provider_factory_returns_correct_client():
    cfg = AIConfig(openai_api_key="sk", hf_api_token="hf")

    openai_client = AIProviderFactory.create(OPENAI_PROVIDER, cfg)
    hf_client = AIProviderFactory.create(HUGGINGFACE_PROVIDER, cfg)

    assert isinstance(openai_client, OpenAIClient)
    assert isinstance(hf_client, HuggingFaceClient)
