from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Optional

DEFAULT_AI_DIR = r"C:\MyDemands\ai_writing"
HF_PROVIDER = "huggingface"
OPENAI_PROVIDER = "openai"
DEFAULT_PROVIDER = HF_PROVIDER
CONFIG_FILE_NAME_BY_PROVIDER = {
    HF_PROVIDER: "configIA.txt",
    OPENAI_PROVIDER: "configOpenAI.txt",
}
CACHE_FILE_NAME_BY_PROVIDER = {
    HF_PROVIDER: "cacheIA.json",
    OPENAI_PROVIDER: "cacheOpenAI.json",
}
MAX_CACHE_ENTRIES = 1000


@dataclass
class AIConfig:
    hf_api_token: str = ""
    hf_model: str = "google/flan-t5-base"
    temperature: float = 0.5
    max_new_tokens: int = 150
    top_p: float = 0.9
    ia_usage_count: int = 0
    ia_usage_limit: int = 200
    ia_last_reset: str = "2026-01-01"
    ia_cache_enabled: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    @property
    def last_reset_date(self) -> date:
        try:
            return datetime.strptime(self.ia_last_reset, "%Y-%m-%d").date()
        except ValueError:
            return date.today()

    @property
    def next_reset_date(self) -> date:
        return self.last_reset_date + timedelta(days=30)


class AIConfigStore:
    def __init__(self, ai_dir: Optional[str] = None):
        self.ai_dir = ai_dir or os.getenv("MYDEMANDS_AI_DIR", DEFAULT_AI_DIR)
        self.legacy_config_path = os.path.join(self.ai_dir, "configIA.txt")
        self.legacy_cache_path = os.path.join(self.ai_dir, "cacheIA.json")

    def _provider_dir(self, provider: str) -> str:
        return os.path.join(self.ai_dir, provider)

    def _config_path(self, provider: str) -> str:
        return os.path.join(self._provider_dir(provider), CONFIG_FILE_NAME_BY_PROVIDER.get(provider, "configIA.txt"))

    def _cache_path(self, provider: str) -> str:
        return os.path.join(self._provider_dir(provider), CACHE_FILE_NAME_BY_PROVIDER.get(provider, "cacheIA.json"))

    def ensure_files(self, provider: str = DEFAULT_PROVIDER) -> None:
        provider_dir = self._provider_dir(provider)
        os.makedirs(provider_dir, exist_ok=True)

        config_path = self._config_path(provider)
        cache_path = self._cache_path(provider)

        if provider == HF_PROVIDER and os.path.exists(self.legacy_config_path) and not os.path.exists(config_path):
            os.replace(self.legacy_config_path, config_path)
        if provider == HF_PROVIDER and os.path.exists(self.legacy_cache_path) and not os.path.exists(cache_path):
            os.replace(self.legacy_cache_path, cache_path)

        if not os.path.exists(config_path):
            default_cfg = AIConfig()
            if provider == OPENAI_PROVIDER:
                lines = [
                    f"OPENAI_API_KEY={default_cfg.openai_api_key}",
                    f"OPENAI_MODEL={default_cfg.openai_model}",
                    f"temperature={default_cfg.temperature}",
                    f"max_new_tokens={default_cfg.max_new_tokens}",
                    f"top_p={default_cfg.top_p}",
                    f"IA_USAGE_COUNT={default_cfg.ia_usage_count}",
                    f"IA_USAGE_LIMIT={default_cfg.ia_usage_limit}",
                    f"IA_LAST_RESET={default_cfg.ia_last_reset}",
                    "IA_CACHE_ENABLED=true",
                ]
            else:
                lines = [
                    f"HF_API_TOKEN={default_cfg.hf_api_token}",
                    f"HF_MODEL={default_cfg.hf_model}",
                    f"temperature={default_cfg.temperature}",
                    f"max_new_tokens={default_cfg.max_new_tokens}",
                    f"top_p={default_cfg.top_p}",
                    f"IA_USAGE_COUNT={default_cfg.ia_usage_count}",
                    f"IA_USAGE_LIMIT={default_cfg.ia_usage_limit}",
                    f"IA_LAST_RESET={default_cfg.ia_last_reset}",
                    "IA_CACHE_ENABLED=true",
                ]
            with open(config_path, "w", encoding="utf-8") as fp:
                fp.write("\n".join(lines) + "\n")
        if not os.path.exists(cache_path):
            with open(cache_path, "w", encoding="utf-8") as fp:
                json.dump({}, fp)

    def load_config(self, provider: str = DEFAULT_PROVIDER) -> AIConfig:
        self.ensure_files(provider)
        parsed: Dict[str, str] = {}
        with open(self._config_path(provider), "r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                parsed[key.strip()] = value.strip()

        cfg = AIConfig(
            hf_api_token=parsed.get("HF_API_TOKEN", ""),
            hf_model=parsed.get("HF_MODEL", AIConfig.hf_model),
            openai_api_key=parsed.get("OPENAI_API_KEY", ""),
            openai_model=parsed.get("OPENAI_MODEL", AIConfig.openai_model),
            temperature=_to_float(parsed.get("temperature"), AIConfig.temperature),
            max_new_tokens=_to_int(parsed.get("max_new_tokens"), AIConfig.max_new_tokens),
            top_p=_to_float(parsed.get("top_p"), AIConfig.top_p),
            ia_usage_count=_to_int(parsed.get("IA_USAGE_COUNT"), AIConfig.ia_usage_count),
            ia_usage_limit=max(1, _to_int(parsed.get("IA_USAGE_LIMIT"), AIConfig.ia_usage_limit)),
            ia_last_reset=parsed.get("IA_LAST_RESET", AIConfig.ia_last_reset),
            ia_cache_enabled=_to_bool(parsed.get("IA_CACHE_ENABLED"), AIConfig.ia_cache_enabled),
        )
        return cfg

    def save_config(self, cfg: AIConfig, provider: str = DEFAULT_PROVIDER) -> None:
        self.ensure_files(provider)
        common_lines = [
            f"temperature={float(cfg.temperature)}",
            f"max_new_tokens={int(cfg.max_new_tokens)}",
            f"top_p={float(cfg.top_p)}",
            f"IA_USAGE_COUNT={int(cfg.ia_usage_count)}",
            f"IA_USAGE_LIMIT={max(1, int(cfg.ia_usage_limit))}",
            f"IA_LAST_RESET={cfg.ia_last_reset}",
            f"IA_CACHE_ENABLED={'true' if cfg.ia_cache_enabled else 'false'}",
        ]
        if provider == OPENAI_PROVIDER:
            lines = [
                f"OPENAI_API_KEY={cfg.openai_api_key.strip()}",
                f"OPENAI_MODEL={cfg.openai_model.strip() or AIConfig.openai_model}",
                *common_lines,
            ]
        else:
            lines = [
                f"HF_API_TOKEN={cfg.hf_api_token.strip()}",
                f"HF_MODEL={cfg.hf_model.strip() or AIConfig.hf_model}",
                *common_lines,
            ]
        with open(self._config_path(provider), "w", encoding="utf-8") as fp:
            fp.write("\n".join(lines) + "\n")

    def load_cache(self, provider: str = DEFAULT_PROVIDER) -> Dict[str, Dict[str, str]]:
        self.ensure_files(provider)
        try:
            with open(self._cache_path(provider), "r", encoding="utf-8") as fp:
                payload = json.load(fp)
            return payload if isinstance(payload, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def save_cache(self, cache: Dict[str, Dict[str, str]], provider: str = DEFAULT_PROVIDER) -> None:
        self.ensure_files(provider)
        with open(self._cache_path(provider), "w", encoding="utf-8") as fp:
            json.dump(cache, fp, ensure_ascii=False, indent=2)

    def reset_usage_if_needed(self, cfg: AIConfig, provider: str = DEFAULT_PROVIDER) -> AIConfig:
        if date.today() >= cfg.next_reset_date:
            cfg.ia_usage_count = 0
            cfg.ia_last_reset = date.today().strftime("%Y-%m-%d")
            self.save_config(cfg, provider=provider)
        return cfg

    def increment_usage(self, cfg: AIConfig, provider: str = DEFAULT_PROVIDER) -> AIConfig:
        cfg.ia_usage_count += 1
        self.save_config(cfg, provider=provider)
        return cfg

    @staticmethod
    def build_cache_key(prompt: str, model: str, temperature: float) -> str:
        payload = f"{prompt}|{model}|{temperature}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def get_cached_response(self, key: str, provider: str = DEFAULT_PROVIDER) -> Optional[str]:
        cache = self.load_cache(provider)
        entry = cache.get(key)
        if isinstance(entry, dict):
            return str(entry.get("response", ""))
        return None

    def save_cache_response(self, key: str, response: str, provider: str = DEFAULT_PROVIDER) -> None:
        cache = self.load_cache(provider)
        cache[key] = {
            "response": response,
            "timestamp": datetime.now().replace(microsecond=0).isoformat(),
        }
        if len(cache) > MAX_CACHE_ENTRIES:
            ordered = sorted(
                cache.items(),
                key=lambda item: item[1].get("timestamp", ""),
            )
            overflow = len(cache) - MAX_CACHE_ENTRIES
            for old_key, _ in ordered[:overflow]:
                cache.pop(old_key, None)
        self.save_cache(cache, provider)


def _to_int(value: Optional[str], fallback: int) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return fallback


def _to_float(value: Optional[str], fallback: float) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return fallback


def _to_bool(value: Optional[str], fallback: bool) -> bool:
    if value is None:
        return fallback
    return str(value).strip().lower() in {"1", "true", "sim", "yes", "on"}
