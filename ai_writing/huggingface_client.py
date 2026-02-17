from __future__ import annotations

import json
import importlib
import importlib.util
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
        self._use_legacy_endpoint = True

    @staticmethod
    def sanitize_text(text: str) -> str:
        return (text or "").replace("\x00", " ").strip()[:6000]

    def build_prompt(self, input_text: str, instruction: str, context: Optional[dict]) -> str:
        sanitized = self.sanitize_text(input_text)
        if not sanitized:
            raise AIWritingError("Texto vazio para sugestão.")
        return f"{instruction}\n\nContexto: {context or {}}\n\nTexto:\n{sanitized}"

    def _legacy_model_url(self) -> str:
        return f"https://api-inference.huggingface.co/models/{self.model}"

    def _router_model_url(self) -> str:
        return f"https://router.huggingface.co/hf-inference/models/{self.model}"

    def _iter_model_urls(self):
        if self._use_legacy_endpoint:
            yield self._legacy_model_url()
        yield self._router_model_url()

    @staticmethod
    def _extract_http_error_message(exc: urllib.error.HTTPError) -> str:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            return ""
        if not body:
            return ""
        try:
            payload = json.loads(body)
        except Exception:
            return body.strip()
        if isinstance(payload, dict) and payload.get("error"):
            return str(payload.get("error")).strip()
        return body.strip()

    def _raise_http_error(self, exc: urllib.error.HTTPError, *, context: str) -> None:
        detail = self._extract_http_error_message(exc)
        if exc.code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
            raise MissingAPIKeyError("Token inválido") from exc
        if exc.code == HTTPStatus.NOT_FOUND:
            raise ModelNotFoundError("Modelo não encontrado") from exc
        if exc.code == HTTPStatus.TOO_MANY_REQUESTS:
            raise RateLimitError("Rate limit") from exc
        if exc.code == HTTPStatus.GONE:
            raise AIWritingError("Endpoint descontinuado (migrado para router)") from exc
        suffix = f": {detail}" if detail else ""
        raise AIWritingError(f"{context} (HTTP {exc.code}){suffix}") from exc

    def _request_inference(self, prompt: str, *, connectivity_check: bool = False) -> dict | list:
        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": self.temperature,
                "max_new_tokens": self.max_new_tokens,
            },
        }
        if self.top_p is not None:
            payload["parameters"]["top_p"] = float(self.top_p)

        last_error: Optional[Exception] = None
        legacy_deprecated = False

        for url in self._iter_model_urls():
            local_payload = dict(payload)
            if url.startswith("https://api-inference.huggingface.co/"):
                local_payload["options"] = {"wait_for_model": True}

            req = urllib.request.Request(
                url,
                data=json.dumps(local_payload).encode("utf-8"),
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
                if exc.code == HTTPStatus.GONE and url.startswith("https://api-inference.huggingface.co/"):
                    self._use_legacy_endpoint = False
                    legacy_deprecated = True
                    last_error = exc
                    continue
                self._raise_http_error(exc, context="Falha na API do Hugging Face")
            except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                raise AIRequestTimeoutError("Timeout") from exc

        if legacy_deprecated:
            msg = "Endpoint antigo foi descontinuado; usando router.huggingface.co/hf-inference"
            if connectivity_check:
                msg = f"Falha no teste de conectividade: {msg}"
            raise AIWritingError(msg) from last_error
        raise AIWritingError("Falha na API do Hugging Face")

    def _validate_token_if_available(self) -> None:
        if importlib.util.find_spec("huggingface_hub") is None:
            return
        module = importlib.import_module("huggingface_hub")
        hf_api_class = getattr(module, "HfApi", None)
        if hf_api_class is None:
            return
        try:
            hf_api_class().whoami(token=self.api_token)
        except Exception as exc:
            text = str(exc).lower()
            if "401" in text or "403" in text or "unauthorized" in text or "forbidden" in text:
                raise MissingAPIKeyError("Token inválido") from exc

    def suggest(self, input_text: str, instruction: str, context: Optional[dict] = None) -> str:
        if not self.api_token:
            raise MissingAPIKeyError("Token do Hugging Face não configurado")
        raw = self._request_inference(self.build_prompt(input_text, instruction, context))

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
        self._validate_token_if_available()
        self._request_inference(
            self.build_prompt("ping", "Responda com uma palavra: OK", {"healthcheck": True}),
            connectivity_check=True,
        )
