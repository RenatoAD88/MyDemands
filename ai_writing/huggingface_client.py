from __future__ import annotations

import importlib.util
import json
import socket
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, Optional

from ai_writing.errors import (
    AIRequestTimeoutError,
    AIWritingError,
    MissingAPIKeyError,
    ModelNotFoundError,
    RateLimitError,
)
from ai_writing.error_log import append_ai_error_log

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

    @staticmethod
    def _safe_get(value: Any, key: str) -> Any:
        if isinstance(value, Mapping):
            return value.get(key)
        return getattr(value, key, None)

    @classmethod
    def _extract_text_content(cls, resp: Any) -> str:
        choices = cls._safe_get(resp, "choices")
        first_choice = choices[0] if isinstance(choices, list) and choices else None

        message = cls._safe_get(first_choice, "message")
        if isinstance(message, str):
            return message

        content = cls._safe_get(message, "content")
        if isinstance(content, str):
            return content

        text_value = cls._safe_get(first_choice, "text")
        if isinstance(text_value, str):
            return text_value

        if isinstance(resp, Mapping):
            resp_choices = resp.get("choices")
            if isinstance(resp_choices, list) and resp_choices:
                resp_choice = resp_choices[0] if isinstance(resp_choices[0], Mapping) else {}
                resp_message = resp_choice.get("message") if isinstance(resp_choice, Mapping) else {}
                if isinstance(resp_message, Mapping):
                    resp_content = resp_message.get("content")
                    if isinstance(resp_content, str):
                        return resp_content

        if isinstance(resp, list):
            for item in resp:
                if isinstance(item, Mapping):
                    generated_text = item.get("generated_text")
                    if isinstance(generated_text, str):
                        return generated_text

        for key in ("generated_text", "output_text", "text"):
            value = cls._safe_get(resp, key)
            if isinstance(value, str):
                return value

        return ""

    @staticmethod
    def _sanitize_for_log(data: Any) -> Any:
        sensitive_keywords = ("token", "authorization", "api_key", "key")
        if isinstance(data, Mapping):
            sanitized: dict[str, Any] = {}
            for key, value in data.items():
                lowered = str(key).lower()
                if any(word in lowered for word in sensitive_keywords):
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = HuggingFaceClient._sanitize_for_log(value)
            return sanitized
        if isinstance(data, list):
            return [HuggingFaceClient._sanitize_for_log(item) for item in data]
        return data

    def _log_unexpected_response(self, response: Any, context: Optional[dict]) -> None:
        context_data = context or {}
        log_context = {
            "provider": "huggingface",
            "model": self.model,
            "demand_id": context_data.get("demand_id"),
            "field": context_data.get("field"),
        }
        sanitized_response = self._sanitize_for_log(response)
        try:
            response_dump = json.dumps(sanitized_response, ensure_ascii=False, default=str)[:4000]
        except Exception:
            response_dump = str(sanitized_response)[:4000]

        append_ai_error_log(
            "Resposta inesperada do provider Hugging Face Router.",
            traceback_text=f"response_dump={response_dump}",
            context=log_context,
            provider="huggingface",
        )

    def _chat_completion(
        self,
        *,
        user_message: str,
        system_message: str,
        max_tokens: Optional[int] = None,
        context: Optional[dict] = None,
    ) -> str:
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
            raise AIWritingError(str(exc) or "Falha na API do Hugging Face") from exc

        if isinstance(completion, Mapping) and completion.get("error"):
            error_data = completion.get("error")
            if isinstance(error_data, Mapping):
                error_message = str(error_data.get("message") or error_data.get("error") or error_data)
            else:
                error_message = str(error_data)
            raise AIWritingError(error_message or "Falha na API do Hugging Face")

        text = self._extract_text_content(completion).strip()
        if not text:
            self._log_unexpected_response(completion, context=context)
            raise AIWritingError("Resposta do provedor não contém texto (formato inesperado). Veja logs.")
        return text

    def suggest(self, input_text: str, instruction: str, context: Optional[dict] = None) -> str:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")

        return self._chat_completion(
            system_message=str(instruction or "").strip() or HF_SYSTEM_PROMPT,
            user_message=self.build_prompt(input_text, instruction, context),
            context=context,
        )

    def check_connectivity(self) -> None:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")

        response = self._chat_completion(system_message="Responda apenas: OK", user_message="ping", max_tokens=16)
        if not response:
            raise AIWritingError("Falha no teste de conectividade: resposta vazia")
