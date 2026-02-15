from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, Optional

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


class OpenAIWritingClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5.2",
        temperature: float = 0.3,
        timeout: float = 30.0,
        max_retries: int = 5,
    ):
        self.model = model
        self.temperature = float(temperature)
        self.timeout = float(timeout)
        self.max_retries = int(max_retries)
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if OpenAI is None:
            self.client = None
            return

        self.client = OpenAI(api_key=self._api_key) if self._api_key else OpenAI()

    @staticmethod
    def sanitize_text(text: str) -> str:
        cleaned = (text or "").replace("\x00", " ").strip()
        return cleaned[:4000]

    def suggest(self, input_text: str, instruction: str, context: Optional[Dict[str, Any]] = None) -> str:
        if self.client is None:
            raise MissingOpenAIDependencyError(
                "Dependência 'openai' não encontrada. Instale com: pip install openai"
            )

        if not self._api_key:
            raise MissingAPIKeyError("Chave não configurada")

        sanitized = self.sanitize_text(input_text)
        if not sanitized:
            raise AIWritingError("Texto vazio para sugestão.")

        payload = [
            {"role": "system", "content": instruction},
            {
                "role": "user",
                "content": f"Contexto: {context or {}}\n\nTexto:\n{sanitized}",
            },
        ]

        attempt = 0
        while True:
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=payload,
                    temperature=self.temperature,
                    timeout=self.timeout,
                )
                output_text = (getattr(response, "output_text", "") or "").strip()
                if output_text:
                    return output_text
                raise AIWritingError("Resposta sem conteúdo textual.")
            except Exception as exc:
                message = str(exc).lower()
                status_code = getattr(exc, "status_code", None)
                attempt += 1

                if "api key" in message and ("missing" in message or "not set" in message or "401" in message):
                    raise MissingAPIKeyError("Chave não configurada") from exc

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
