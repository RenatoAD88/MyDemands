from __future__ import annotations

from typing import Any, Dict

from ai_writing.config_store import AIConfigStore, DEFAULT_PROVIDER
from ai_writing.errors import UsageLimitReachedError
from ai_writing.openai_client import OpenAIClient


class AIWritingService:
    def __init__(self, config_store: AIConfigStore | None = None):
        self.config_store = config_store or AIConfigStore()

    @staticmethod
    def _resolve_client(provider: str):
        return OpenAIClient

    def generate(self, input_text: str, instruction: str, context: Dict[str, Any], provider: str = DEFAULT_PROVIDER) -> str:
        cfg = self.config_store.reset_usage_if_needed(self.config_store.load_config(provider=provider), provider=provider)
        if cfg.ia_usage_count >= cfg.ia_usage_limit:
            raise UsageLimitReachedError("Limite mensal de uso da IA atingido")

        client = self._resolve_client(provider)(
            api_key=cfg.openai_api_key,
            model=cfg.openai_model,
            temperature=cfg.temperature,
            max_new_tokens=cfg.max_new_tokens,
            top_p=cfg.top_p,
        )

        prompt = client.build_prompt(input_text=input_text, instruction=instruction, context=context)
        cache_key = self.config_store.build_cache_key(prompt, cfg.openai_model, cfg.temperature)

        if cfg.ia_cache_enabled:
            cached = self.config_store.get_cached_response(cache_key, provider=provider)
            if cached:
                return cached

        response = client.suggest(input_text=input_text, instruction=instruction, context=context)
        if cfg.ia_cache_enabled:
            self.config_store.save_cache_response(cache_key, response, provider=provider)
        self.config_store.increment_usage(cfg, provider=provider)
        return response
