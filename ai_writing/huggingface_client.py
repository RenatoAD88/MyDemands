from __future__ import annotations

import importlib.util
import json
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

HF_ROUTER_BASE_URL = "https://router.huggingface.co/v1"
HF_SYSTEM_PROMPT = "Você é um assistente que reescreve textos corporativos em português do Brasil."


class HuggingFaceClient:
    def __init__(
        self,
        api_token: str,
        model: str = "zai-org/GLM-5:novita",
        temperature: float = 0.5,
        max_new_tokens: int = 150,
        top_p: Optional[float] = 0.9,
        timeout: float = 30.0,
    ):
        self.api_token = (api_token or "").strip()
        self.model = model.strip() or "zai-org/GLM-5:novita"
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
    def _extract_exception_metadata(exc: Exception) -> dict:
        response = getattr(exc, "response", None)
        status_code = getattr(exc, "status_code", None)
        if status_code is None and response is not None:
            status_code = getattr(response, "status_code", None)

        body_text = ""
        body_json = None
        if response is not None:
            body_text = str(getattr(response, "text", "") or "").strip()
            if not body_text:
                data = getattr(response, "content", b"")
                if isinstance(data, bytes):
                    body_text = data.decode("utf-8", errors="replace").strip()
                elif data is not None:
                    body_text = str(data).strip()
            if body_text:
                try:
                    body_json = json.loads(body_text)
                except (TypeError, ValueError):
                    body_json = None

        if not body_text:
            body_text = str(exc).strip()

        if not body_text:
            body_text = exc.__class__.__name__

        return {
            "status_code": status_code,
            "body": body_text,
            "json": body_json,
        }

    @staticmethod
    def _matches_any(text: str, *needles: str) -> bool:
        lowered = text.lower()
        return any(needle.lower() in lowered for needle in needles)

    def _map_hf_error(self, exc: Exception) -> AIWritingError:
        metadata = self._extract_exception_metadata(exc)
        status_code = metadata.get("status_code")
        detail = str(metadata.get("body", "") or "")

        if status_code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
            mapped: AIWritingError = MissingAPIKeyError("Credencial inválida: verifique o token da Hugging Face")
        elif status_code == HTTPStatus.NOT_FOUND:
            mapped = ModelNotFoundError("Modelo/provider inválido no Hugging Face Router")
        elif status_code == HTTPStatus.TOO_MANY_REQUESTS:
            mapped = RateLimitError("Rate limit da Hugging Face atingido")
        elif self._matches_any(detail, "not supported by any provider", "no provider"):
            mapped = ModelNotFoundError("Modelo/provider inválido no Hugging Face Router")
        else:
            mapped = AIWritingError(detail or "Falha na API do Hugging Face")

        setattr(mapped, "hf_error_details", metadata)
        setattr(mapped, "hf_model", self.model)
        return mapped

    def _create_router_client(self):
        if importlib.util.find_spec("openai") is None:
            raise AIWritingError("Dependência ausente: instale openai")

        from openai import OpenAI

        return OpenAI(base_url=HF_ROUTER_BASE_URL, api_key=self.api_token, timeout=self.timeout)

    def _chat_completion(self, *, user_message: str, system_message: str, max_tokens: Optional[int] = None) -> str:
        client = self._create_router_client()

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            "temperature": self.temperature,
            "max_tokens": int(max_tokens if max_tokens is not None else self.max_new_tokens),
        }
        if self.top_p is not None:
            payload["top_p"] = float(self.top_p)

        try:
            completion = client.chat.completions.create(**payload)
        except (TimeoutError, socket.timeout) as exc:
            raise AIRequestTimeoutError("Timeout/rede") from exc
        except Exception as exc:
            if "timeout" in str(exc).lower():
                raise AIRequestTimeoutError("Timeout/rede") from exc
            raise self._map_hf_error(exc) from exc

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
            system_message=str(instruction or "").strip() or HF_SYSTEM_PROMPT,
            user_message=self.build_prompt(input_text, instruction, context),
        )

    def check_connectivity(self) -> None:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")

        response = self._chat_completion(system_message="Responda apenas: OK", user_message="ping", max_tokens=16)
        if not response:
            raise AIWritingError("Falha no teste de conectividade: resposta vazia")
