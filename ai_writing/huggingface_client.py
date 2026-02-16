from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from http import HTTPStatus
from typing import Optional




DEFAULT_CONNECTIVITY_URL = "https://huggingface.co/api/whoami-v2"

LEGACY_MODEL_ALIASES = {
    "mistralai/Mistral-7B-Instruct-v0.2": "mistralai/Mistral-7B-Instruct-v0.3",
}

class AIWritingError(RuntimeError):
    pass


class MissingAPIKeyError(AIWritingError):
    pass


class ModelNotFoundError(AIWritingError):
    pass


class RateLimitError(AIWritingError):
    pass


class AIRequestTimeoutError(AIWritingError):
    pass


class UsageLimitReachedError(AIWritingError):
    pass


class HuggingFaceClient:
    def __init__(
        self,
        api_token: str,
        model: str = "mistralai/Mistral-7B-Instruct-v0.3",
        temperature: float = 0.5,
        max_new_tokens: int = 150,
        top_p: Optional[float] = None,
        timeout: float = 30.0,
    ):
        self.api_token = (api_token or "").strip()
        self.model = model.strip() or "mistralai/Mistral-7B-Instruct-v0.3"
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

    def suggest(self, input_text: str, instruction: str, context: Optional[dict] = None) -> str:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")

        prompt = self.build_prompt(input_text, instruction, context)
        parameters = {
            "temperature": self.temperature,
            "max_new_tokens": self.max_new_tokens,
        }
        if self.top_p is not None:
            parameters["top_p"] = float(self.top_p)

        payload = {
            "inputs": prompt,
            "parameters": parameters,
        }

        raw = self._request_with_fallback(payload)

        return self._extract_text(raw, prompt)

    def _request_with_fallback(self, payload: dict):
        last_http_error = None
        candidate_models = [self.model]
        alias_model = LEGACY_MODEL_ALIASES.get(self.model)
        if alias_model and alias_model not in candidate_models:
            candidate_models.append(alias_model)

        for model in candidate_models:
            endpoints = [
                f"https://api-inference.huggingface.co/models/{model}",
                f"https://router.huggingface.co/hf-inference/models/{model}",
            ]
            for idx, endpoint in enumerate(endpoints):
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )

                try:
                    with urllib.request.urlopen(req, timeout=self.timeout) as response:
                        return json.loads(response.read().decode("utf-8"))
                except urllib.error.HTTPError as exc:
                    last_http_error = exc
                    if exc.code == 401:
                        raise MissingAPIKeyError("Token do Hugging Face inválido ou ausente") from exc
                    if exc.code == 404:
                        if model != candidate_models[-1]:
                            break
                        raise ModelNotFoundError("Modelo do Hugging Face não encontrado") from exc
                    if exc.code == 429:
                        raise RateLimitError("Limite de requisições do Hugging Face atingido") from exc
                    if exc.code == 410 and idx == 0:
                        continue
                    raise AIWritingError(f"Falha na API do Hugging Face (HTTP {exc.code})") from exc
                except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                    raise AIRequestTimeoutError("Timeout na API do Hugging Face") from exc

        if isinstance(last_http_error, urllib.error.HTTPError) and last_http_error.code == 410:
            raise AIWritingError("Falha na API do Hugging Face (HTTP 410)") from last_http_error

        raise AIWritingError("Falha inesperada ao chamar a API do Hugging Face")

    def check_connectivity(self) -> None:
        req = urllib.request.Request(
            DEFAULT_CONNECTIVITY_URL,
            headers={"Authorization": f"Bearer {self.api_token}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout):
                return
        except urllib.error.HTTPError as exc:
            if exc.code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                raise MissingAPIKeyError("Token do Hugging Face inválido ou ausente") from exc
            raise AIWritingError(f"Falha ao validar conectividade (HTTP {exc.code})") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise AIRequestTimeoutError("Timeout na API do Hugging Face") from exc

    @staticmethod
    def _extract_text(payload, prompt: str) -> str:
        if isinstance(payload, dict) and payload.get("error"):
            raise AIWritingError(str(payload.get("error")))

        if isinstance(payload, list) and payload:
            first = payload[0]
            if isinstance(first, dict):
                text = str(first.get("generated_text", "")).strip()
                if text.startswith(prompt):
                    text = text[len(prompt):].strip()
                if text:
                    return text

        raise AIWritingError("Resposta sem conteúdo textual.")
