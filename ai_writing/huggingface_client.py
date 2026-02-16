from __future__ import annotations

import socket
from typing import Optional

from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError


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
        model: str = "google/flan-t5-base",
        temperature: float = 0.5,
        max_new_tokens: int = 150,
        top_p: Optional[float] = None,
        timeout: float = 30.0,
    ):
        self.api_token = (api_token or "").strip()
        self.model = model.strip() or "google/flan-t5-base"
        self.temperature = float(temperature)
        self.max_new_tokens = int(max_new_tokens)
        self.top_p = top_p
        self.timeout = float(timeout)
        self._client = InferenceClient(api_key=self.api_token, timeout=self.timeout)

    @staticmethod
    def sanitize_text(text: str) -> str:
        return (text or "").replace("\x00", " ").strip()[:6000]

    def build_prompt(self, input_text: str, instruction: str, context: Optional[dict]) -> str:
        sanitized = self.sanitize_text(input_text)
        if not sanitized:
            raise AIWritingError("Texto vazio para sugestão.")
        return f"{instruction}\n\nContexto: {context or {}}\n\nTexto:\n{sanitized}"

    def suggest(self, input_text: str, instruction: str, context: Optional[dict] = None) -> str:
        self._ensure_api_key()

        prompt = self.build_prompt(input_text, instruction, context)
        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": prompt},
        ]
        completion = self._chat_completion(messages=messages)
        return self._extract_text(completion)

    def check_connectivity(self) -> None:
        self._ensure_api_key()

        messages = [{"role": "user", "content": "ping"}]
        completion = self._chat_completion(messages=messages, max_tokens=min(self.max_new_tokens, 16))
        content = self._extract_text(completion)
        if not content.strip():
            raise AIWritingError("Teste de conectividade falhou: resposta vazia do modelo.")

    def _ensure_api_key(self) -> None:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")

    def _chat_completion(self, messages: list[dict[str, str]], max_tokens: Optional[int] = None):
        request_max_tokens = int(max_tokens if max_tokens is not None else self.max_new_tokens)
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": request_max_tokens,
        }
        if self.top_p is not None:
            payload["top_p"] = float(self.top_p)

        try:
            return self._client.chat.completions.create(**payload)
        except Exception as exc:  # noqa: BLE001
            raise self._map_exception(exc) from exc

    @staticmethod
    def _extract_text(completion) -> str:
        choices = getattr(completion, "choices", None)
        if choices is None and isinstance(completion, dict):
            choices = completion.get("choices")

        if not choices:
            raise AIWritingError("Resposta sem conteúdo textual.")

        first = choices[0]
        message = getattr(first, "message", None)
        if message is None and isinstance(first, dict):
            message = first.get("message")

        content = getattr(message, "content", None)
        if content is None and isinstance(message, dict):
            content = message.get("content")

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get("text", "")).strip())
                else:
                    parts.append(str(item).strip())
            content = " ".join(part for part in parts if part).strip()

        text = str(content or "").strip()
        if not text:
            raise AIWritingError("Resposta sem conteúdo textual.")
        return text

    @staticmethod
    def _map_exception(exc: Exception) -> AIWritingError:
        response = getattr(exc, "response", None)
        status_code = getattr(exc, "status_code", None)
        if status_code is None and response is not None:
            status_code = getattr(response, "status_code", None)

        message = str(exc)

        if status_code in {401, 403}:
            return MissingAPIKeyError("Token do Hugging Face inválido ou ausente")
        if status_code == 404:
            return ModelNotFoundError("Modelo do Hugging Face não encontrado")
        if status_code == 429:
            return RateLimitError("Limite de requisições do Hugging Face atingido")

        timeout_markers = ("timeout", "timed out", "connection", "temporarily unavailable")
        lowered_message = message.lower()
        if isinstance(exc, (TimeoutError, socket.timeout)):
            return AIRequestTimeoutError("Timeout na API do Hugging Face")
        if isinstance(exc, OSError) and any(marker in lowered_message for marker in timeout_markers):
            return AIRequestTimeoutError("Timeout na API do Hugging Face")
        if isinstance(exc, HfHubHTTPError) and status_code is None:
            if any(marker in lowered_message for marker in timeout_markers):
                return AIRequestTimeoutError("Timeout na API do Hugging Face")

        return AIWritingError(message or "Falha inesperada ao chamar a API do Hugging Face")
