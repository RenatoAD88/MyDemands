from __future__ import annotations

from typing import Dict, Any

from ai_writing.config_store import AIConfigStore, DEFAULT_PROVIDER, HF_PROVIDER, OPENAI_PROVIDER
from ai_writing.huggingface_client import HuggingFaceClient, UsageLimitReachedError
from ai_writing.openai_client import OpenAIClient


class AIWritingService:
    def __init__(self, config_store: AIConfigStore | None = None):
        self.config_store = config_store or AIConfigStore()

    @staticmethod
    def _resolve_client(provider: str):
        if provider == OPENAI_PROVIDER:
            return OpenAIClient
        return HuggingFaceClient

    def generate(self, input_text: str, instruction: str, context: Dict[str, Any], provider: str = DEFAULT_PROVIDER) -> str:
        cfg = self.config_store.reset_usage_if_needed(self.config_store.load_config(provider=provider), provider=provider)
        if cfg.ia_usage_count >= cfg.ia_usage_limit:
            raise UsageLimitReachedError("Limite mensal de uso da IA atingido")

        client_cls = self._resolve_client(provider)
        if provider == OPENAI_PROVIDER:
            client = client_cls(
                api_key=cfg.openai_api_key,
                model=cfg.openai_model,
                temperature=cfg.temperature,
                max_new_tokens=cfg.max_new_tokens,
                top_p=cfg.top_p,
            )
            model_name = cfg.openai_model
        else:
            client = client_cls(
                api_token=cfg.hf_api_token,
                model=cfg.hf_model,
                temperature=cfg.temperature,
                max_new_tokens=cfg.max_new_tokens,
                top_p=cfg.top_p,
            )
            model_name = cfg.hf_model

        prompt = client.build_prompt(input_text=input_text, instruction=instruction, context=context)
        cache_key = self.config_store.build_cache_key(prompt, model_name, cfg.temperature)

        if cfg.ia_cache_enabled:
            cached = self.config_store.get_cached_response(cache_key, provider=provider)
            if cached:
                return cached

        response = client.suggest(input_text=input_text, instruction=instruction, context=context)
        if cfg.ia_cache_enabled:
            self.config_store.save_cache_response(cache_key, response, provider=provider)
        self.config_store.increment_usage(cfg, provider=provider)
        return response
