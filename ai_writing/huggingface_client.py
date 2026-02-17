from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from http import HTTPStatus
from typing import Optional

from ai_writing.errors import (
    AIRequestTimeoutError,
    AIWritingError,
    MissingAPIKeyError,
    ModelNotFoundError,
    RateLimitError,
)


class HuggingFaceClient:
    def __init__(
        self,
        api_token: str,
        model: str = "HuggingFaceH4/zephyr-7b-beta",
        temperature: float = 0.5,
        max_new_tokens: int = 150,
        top_p: Optional[float] = 0.9,
        timeout: float = 30.0,
    ):
        self.api_token = (api_token or "").strip()
        self.model = model.strip() or "HuggingFaceH4/zephyr-7b-beta"
        self.temperature = float(temperature)
        self.max_new_tokens = int(max_new_tokens)
        self.top_p = top_p
        self.timeout = float(timeout)

    @staticmethod
    def sanitize_text(text: str) -> str:
        return (text or "").replace("\x00", " ").strip()[:6000]

    def build_prompt(self, input_text: str, instruction: str, context: Optional[dict]) -> str:
        sanitized = self.sanitize_text(input_text)
        if not sanitized:
            raise AIWritingError("Texto vazio para sugestão.")
        return f"{instruction}\n\nContexto: {context or {}}\n\nTexto:\n{sanitized}"

    def _model_url(self) -> str:
        return f"https://api-inference.huggingface.co/models/{self.model}"

    def suggest(self, input_text: str, instruction: str, context: Optional[dict] = None) -> str:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")

        payload = {
            "inputs": self.build_prompt(input_text, instruction, context),
            "parameters": {
                "temperature": self.temperature,
                "max_new_tokens": self.max_new_tokens,
            },
        }
        if self.top_p is not None:
            payload["parameters"]["top_p"] = float(self.top_p)

        req = urllib.request.Request(
            self._model_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                raise MissingAPIKeyError("Token do Hugging Face inválido ou ausente") from exc
            if exc.code == HTTPStatus.NOT_FOUND:
                raise ModelNotFoundError("Modelo do Hugging Face inválido ou indisponível") from exc
            if exc.code == HTTPStatus.TOO_MANY_REQUESTS:
                raise RateLimitError("Cota/limite do Hugging Face atingido") from exc
            raise AIWritingError(f"Falha na API do Hugging Face (HTTP {exc.code})") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise AIRequestTimeoutError("Timeout/rede ao chamar Hugging Face") from exc

        if isinstance(raw, list) and raw:
            first = raw[0]
            if isinstance(first, dict):
                text = str(first.get("generated_text", "")).strip()
                if text:
                    return text
        if isinstance(raw, dict) and raw.get("error"):
            raise AIWritingError(str(raw.get("error")))
        raise AIWritingError("Resposta sem conteúdo textual.")

    def check_connectivity(self) -> None:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")
        req = urllib.request.Request(
            self._model_url(),
            headers={"Authorization": f"Bearer {self.api_token}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout):
                return
        except urllib.error.HTTPError as exc:
            if exc.code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                raise MissingAPIKeyError("Token do Hugging Face inválido ou ausente") from exc
            if exc.code == HTTPStatus.NOT_FOUND:
                raise ModelNotFoundError("Modelo do Hugging Face inválido ou indisponível") from exc
            if exc.code == HTTPStatus.TOO_MANY_REQUESTS:
                raise RateLimitError("Cota/limite do Hugging Face atingido") from exc
            raise AIWritingError(f"Falha ao validar conectividade Hugging Face (HTTP {exc.code})") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise AIRequestTimeoutError("Timeout/rede ao validar Hugging Face") from exc
