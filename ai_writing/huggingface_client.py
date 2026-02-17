from __future__ import annotations

import socket
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
        model: str = "stepfun-ai/Step-3.5-Flash",
        temperature: float = 0.5,
        max_new_tokens: int = 150,
        top_p: Optional[float] = 0.9,
        timeout: float = 30.0,
    ):
        self.api_token = (api_token or "").strip()
        self.model = model.strip() or "stepfun-ai/Step-3.5-Flash"
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

    @staticmethod
    def _extract_exception_message(exc: Exception) -> str:
        body = getattr(exc, "response", None)
        text = ""
        if body is not None:
            data = getattr(body, "text", None)
            if data:
                text = str(data)
        if not text:
            text = str(exc)
        return text.strip()

    def _raise_hf_error(self, exc: Exception) -> None:
        status_code = getattr(exc, "status_code", None)
        if status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
            raise MissingAPIKeyError("Token inválido/ausente") from exc
        if status_code == HTTPStatus.NOT_FOUND:
            raise ModelNotFoundError("Modelo não encontrado") from exc
        if status_code == HTTPStatus.TOO_MANY_REQUESTS:
            raise RateLimitError("Rate limit") from exc

        detail = self._extract_exception_message(exc).lower()
        if "gated" in detail or "license" in detail or "accept" in detail or "terms" in detail:
            raise AIWritingError("Modelo requer aceite de termos/licença no site da Hugging Face") from exc

        raise AIWritingError(self._extract_exception_message(exc) or "Falha na API do Hugging Face") from exc

    def _chat_completion(self, *, user_message: str, system_message: str) -> str:
        try:
            from huggingface_hub import InferenceClient
            from huggingface_hub.errors import HfHubHTTPError
        except ImportError as exc:
            raise AIWritingError("Dependência ausente: instale huggingface_hub compatível") from exc

        client = InferenceClient(api_key=self.api_token, timeout=self.timeout)
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_new_tokens,
        }
        if self.top_p is not None:
            kwargs["top_p"] = float(self.top_p)

        try:
            completion = client.chat.completions.create(**kwargs)
        except HfHubHTTPError as exc:
            self._raise_hf_error(exc)
        except (TimeoutError, socket.timeout) as exc:
            raise AIRequestTimeoutError("Timeout/rede") from exc
        except Exception as exc:
            message = str(exc).lower()
            if "timeout" in message:
                raise AIRequestTimeoutError("Timeout/rede") from exc
            raise AIWritingError(f"Falha na API do Hugging Face: {exc}") from exc

        try:
            content = completion.choices[0].message.content
        except Exception as exc:
            raise AIWritingError("Resposta sem conteúdo textual.") from exc

        text = str(content or "").strip()
        if not text:
            raise AIWritingError("Resposta sem conteúdo textual.")
        return text

    def suggest(self, input_text: str, instruction: str, context: Optional[dict] = None) -> str:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")
        return self._chat_completion(
            system_message=str(instruction or "").strip() or "Você é um assistente útil.",
            user_message=self.build_prompt(input_text, instruction, context),
        )

    def check_connectivity(self) -> None:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")
        response = self._chat_completion(system_message="Responda apenas: OK", user_message="ping")
        if not str(response).strip():
            raise AIWritingError("Falha no teste de conectividade: resposta vazia")
