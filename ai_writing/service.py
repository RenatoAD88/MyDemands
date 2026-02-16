from __future__ import annotations

from typing import Dict, Any

from ai_writing.config_store import AIConfigStore
from ai_writing.huggingface_client import HuggingFaceClient, UsageLimitReachedError


class AIWritingService:
    def __init__(self, config_store: AIConfigStore | None = None, client_cls=HuggingFaceClient):
        self.config_store = config_store or AIConfigStore()
        self.client_cls = client_cls

    def generate(self, input_text: str, instruction: str, context: Dict[str, Any]) -> str:
        cfg = self.config_store.reset_usage_if_needed(self.config_store.load_config())
        if cfg.ia_usage_count >= cfg.ia_usage_limit:
            raise UsageLimitReachedError("Limite mensal de uso da IA atingido")

        client = self.client_cls(
            api_token=cfg.hf_api_token,
            model=cfg.hf_model,
            temperature=cfg.temperature,
            max_new_tokens=cfg.max_new_tokens,
            top_p=cfg.top_p,
        )

        prompt = client.build_prompt(input_text=input_text, instruction=instruction, context=context)
        cache_key = self.config_store.build_cache_key(prompt, cfg.hf_model, cfg.temperature)

        if cfg.ia_cache_enabled:
            cached = self.config_store.get_cached_response(cache_key)
            if cached:
                return cached

        response = client.suggest(input_text=input_text, instruction=instruction, context=context)
        if cfg.ia_cache_enabled:
            self.config_store.save_cache_response(cache_key, response)
        self.config_store.increment_usage(cfg)
        return response
