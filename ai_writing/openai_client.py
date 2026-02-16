from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from ai_writing.key_store import load_api_key

try:
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - depende do ambiente da máquina
    OpenAI = None


class AIWritingError(RuntimeError):
    pass


class MissingAPIKeyError(AIWritingError):
    pass


class MissingOpenAIDependencyError(AIWritingError):
    pass


class InsufficientQuotaError(AIWritingError):
    pass


class OpenAIWritingClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.3,
        timeout: float = 30.0,
        max_retries: int = 5,
    ):
        self.model = model
        self.temperature = float(temperature)
        self.timeout = float(timeout)
        self.max_retries = int(max_retries)
        self._api_key = (api_key or load_api_key() or os.getenv("OPENAI_API_KEY", "")).strip()
        self.client = (OpenAI(api_key=self._api_key) if OpenAI is not None else None) if self._api_key else None

    @staticmethod
    def sanitize_text(text: str) -> str:
        cleaned = (text or "").replace("\x00", " ").strip()
        return cleaned[:4000]

    def _build_payload(self, instruction: str, context: Optional[Dict[str, Any]], sanitized: str) -> Dict[str, Any]:
        return {
            "model": self.model,
            "input": [
                {"role": "system", "content": instruction},
                {
                    "role": "user",
                    "content": f"Contexto: {context or {}}\n\nTexto:\n{sanitized}",
                },
            ],
            "temperature": self.temperature,
        }

    def _suggest_via_sdk(self, payload: Dict[str, Any]) -> str:
        response = self.client.responses.create(
            model=payload["model"],
            input=payload["input"],
            temperature=payload["temperature"],
            timeout=self.timeout,
        )
        return (getattr(response, "output_text", "") or "").strip()

    def _suggest_via_http(self, payload: Dict[str, Any]) -> str:
        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        output_text = (data.get("output_text") or "").strip()
        if output_text:
            return output_text

        output = data.get("output") or []
        fragments = []
        for item in output:
            for content in item.get("content", []):
                text = (content.get("text") or "").strip()
                if text:
                    fragments.append(text)
        return "\n".join(fragments).strip()

    def suggest(self, input_text: str, instruction: str, context: Optional[Dict[str, Any]] = None) -> str:
        if not self._api_key:
            raise MissingAPIKeyError("Chave não configurada")

        sanitized = self.sanitize_text(input_text)
        if not sanitized:
            raise AIWritingError("Texto vazio para sugestão.")

        payload = self._build_payload(instruction, context, sanitized)

        attempt = 0
        while True:
            try:
                output_text = self._suggest_via_sdk(payload) if self.client is not None else self._suggest_via_http(payload)
                if output_text:
                    return output_text
                raise AIWritingError("Resposta sem conteúdo textual.")
            except urllib.error.HTTPError as exc:
                attempt += 1
                status_code = exc.code
                message = exc.read().decode("utf-8", errors="ignore") if exc.fp else str(exc)
                lowered_message = message.lower()

                if status_code in (401, 403):
                    raise MissingAPIKeyError("Chave não configurada") from exc

                if status_code == 429 and "insufficient_quota" in lowered_message:
                    raise InsufficientQuotaError("Créditos da API esgotados. Verifique seu plano e faturamento da OpenAI.") from exc

                should_retry = status_code == 429 or status_code >= 500
                if should_retry and attempt < self.max_retries:
                    base = min(2 ** attempt, 16)
                    jitter = random.uniform(0, 0.25)
                    time.sleep(base + jitter)
                    continue

                if status_code < 500 and status_code != 429:
                    raise AIWritingError("Falha ao gerar sugestão (erro de requisição).") from exc
                raise AIWritingError(f"Falha ao gerar sugestão (HTTP {status_code}). {lowered_message}") from exc
            except Exception as exc:
                message = str(exc).lower()
                status_code = getattr(exc, "status_code", None)
                attempt += 1

                if "api key" in message and ("missing" in message or "not set" in message or "401" in message):
                    raise MissingAPIKeyError("Chave não configurada") from exc

                if "insufficient_quota" in message and (status_code in (None, 429) or "429" in message):
                    raise InsufficientQuotaError("Créditos da API esgotados. Verifique seu plano e faturamento da OpenAI.") from exc

                should_retry = False
                if status_code == 429 or "429" in message or "rate limit" in message:
                    should_retry = True
                elif status_code and int(status_code) >= 500:
                    should_retry = True
                elif any(token in message for token in ["timeout", "temporar", "connection reset", "service unavailable"]):
                    should_retry = True

                if should_retry and attempt < self.max_retries:
                    base = min(2 ** attempt, 16)
                    jitter = random.uniform(0, 0.25)
                    time.sleep(base + jitter)
                    continue

                if status_code and int(status_code) < 500 and int(status_code) != 429:
                    raise AIWritingError("Falha ao gerar sugestão (erro de requisição).") from exc
                raise AIWritingError("Falha ao gerar sugestão (ver logs)") from exc
