from __future__ import annotations

import json
import socket
import time
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
            if body_text:
                try:
                    body_json = json.loads(body_text)
                except (TypeError, ValueError):
                    body_json = None

        if not body_text:
            body_text = str(exc).strip()

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
            mapped = ModelNotFoundError("Modelo não encontrado")
        elif status_code == HTTPStatus.TOO_MANY_REQUESTS:
            mapped = RateLimitError("Rate limit da Hugging Face atingido")
        elif self._matches_any(detail, "not supported by any provider", "no provider"):
            mapped = AIWritingError(
                "Modelo sem provider compatível no Inference Providers; escolha um modelo com Playground/Providers habilitado"
            )
        elif self._matches_any(detail, "gated", "requires acceptance", "accept", "license", "terms"):
            mapped = AIWritingError(
                "Modelo com acesso restrito; aceite os termos/licença na página do modelo da Hugging Face"
            )
        elif self._matches_any(detail, "loading", "currently loading"):
            mapped = AIWritingError("Modelo está carregando; aguarde e tente novamente")
        else:
            mapped = AIWritingError(detail or "Falha na API do Hugging Face")

        setattr(mapped, "hf_error_details", metadata)
        setattr(mapped, "hf_model", self.model)
        return mapped

    def _create_inference_client(self):
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise AIWritingError("Dependência ausente: instale huggingface_hub compatível no venv") from exc
        return InferenceClient(api_key=self.api_token, timeout=self.timeout)

    def _perform_chat_completion(self, *, user_message: str, system_message: str, retry_on_loading: bool = True):
        try:
            from huggingface_hub.errors import HfHubHTTPError
        except ImportError as exc:
            raise AIWritingError("Dependência ausente: instale huggingface_hub compatível no venv") from exc

        client = self._create_inference_client()
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
            return client.chat.completions.create(**kwargs)
        except HfHubHTTPError as exc:
            mapped = self._map_hf_error(exc)
            if retry_on_loading and self._matches_any(str(mapped), "carregando"):
                time.sleep(0.6)
                return self._perform_chat_completion(
                    user_message=user_message,
                    system_message=system_message,
                    retry_on_loading=False,
                )
            raise mapped from exc
        except (TimeoutError, socket.timeout) as exc:
            raise AIRequestTimeoutError("Timeout/rede") from exc
        except Exception as exc:
            message = str(exc).lower()
            if "timeout" in message:
                raise AIRequestTimeoutError("Timeout/rede") from exc
            raise AIWritingError(f"Falha na API do Hugging Face: {exc}") from exc

    def _chat_completion(self, *, user_message: str, system_message: str) -> str:
        completion = self._perform_chat_completion(user_message=user_message, system_message=system_message)
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

        try:
            from huggingface_hub import HfApi
        except ImportError as exc:
            raise AIWritingError("Dependência ausente: instale huggingface_hub compatível no venv") from exc

        try:
            HfApi().whoami(token=self.api_token)
        except Exception as exc:
            raise self._map_hf_error(exc) from exc

        response = self._chat_completion(system_message="Responda apenas: OK", user_message="ping")
        if not str(response).strip():
            raise AIWritingError("Falha no teste de conectividade: resposta vazia")
