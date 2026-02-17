from __future__ import annotations

from typing import Any, Dict

from ai_writing.config_store import AIConfigStore, DEFAULT_PROVIDER
from ai_writing.errors import AIWritingError, UsageLimitReachedError
from ai_writing.provider_factory import AIProviderFactory


class AIWritingService:
    def __init__(self, config_store: AIConfigStore | None = None):
        self.config_store = config_store or AIConfigStore()

    @staticmethod
    def _resolve_client(provider: str, cfg):
        return AIProviderFactory.create(provider, cfg)

    @staticmethod
    def _is_variation(context: Dict[str, Any]) -> bool:
        return bool((context or {}).get("is_variation"))

    @staticmethod
    def _variation_index(context: Dict[str, Any]) -> int:
        try:
            return int((context or {}).get("variation_index", 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _build_effective_instruction(instruction: str, context: Dict[str, Any]) -> str:
        if not AIWritingService._is_variation(context):
            return instruction
        idx = AIWritingService._variation_index(context)
        return f"{instruction}\n\nVariação: {idx} - Gere uma alternativa diferente."

    def generate(self, input_text: str, instruction: str, context: Dict[str, Any], provider: str = DEFAULT_PROVIDER) -> str:
        cfg = self.config_store.reset_usage_if_needed(self.config_store.load_config(provider=provider), provider=provider)
        if not cfg.ai_enabled:
            raise AIWritingError("IA desativada")
        if cfg.ia_usage_count >= cfg.ia_usage_limit:
            raise UsageLimitReachedError("Limite mensal de uso da IA atingido")

        current_provider = cfg.ai_provider or provider
        client = self._resolve_client(current_provider, cfg)

        model = cfg.openai_model if current_provider == "openai" else cfg.hf_model
        temp = cfg.openai_temperature if current_provider == "openai" else cfg.hf_temperature
        top_p = cfg.hf_top_p if current_provider == "huggingface" else None

        if self._is_variation(context):
            temp = min(1.0, float(temp) + 0.2)
            client.temperature = temp
            if hasattr(client, "top_p"):
                client.top_p = 0.95
                top_p = 0.95

        effective_instruction = self._build_effective_instruction(instruction, context)
        cache_key = self.config_store.build_cache_key(
            provider=current_provider,
            model=model,
            instruction=effective_instruction,
            action=str((context or {}).get("action", "")),
            tone=str((context or {}).get("tone", "")),
            size=str((context or {}).get("size", "")),
            input_text=input_text,
            variation_index=self._variation_index(context),
            temperature=float(temp),
            top_p=top_p,
        )

        if bool((context or {}).get("debug_log_text")):
            print(
                f"[AI][service] provider={current_provider} model={model} temp={temp} top_p={top_p} "
                f"max_tokens={getattr(client, 'max_new_tokens', getattr(client, 'max_output_tokens', None))} "
                f"variation_index={self._variation_index(context)}"
            )

        if cfg.ia_cache_enabled:
            cached = self.config_store.get_cached_response(cache_key, provider=current_provider)
            if cached:
                return cached

        response = client.suggest(input_text=input_text, instruction=effective_instruction, context=context)
        if cfg.ia_cache_enabled:
            self.config_store.save_cache_response(cache_key, response, provider=current_provider)
        self.config_store.increment_usage(cfg, provider=provider)
        return response
