from __future__ import annotations

import json
import re
import socket
import time
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


DEFAULT_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_CONNECTIVITY_URL = "https://api.openai.com/v1/models"
_INVALID_SHORT_OUTPUTS = {"and", "ok", "success"}


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.5,
        max_new_tokens: int = 150,
        top_p: Optional[float] = None,
        timeout: float = 30.0,
    ):
        self.api_key = (api_key or "").strip()
        self.model = model.strip() or "gpt-4o-mini"
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
    def _extract_final_tag(text: str) -> str:
        match = re.search(r"<final>(.*?)</final>", str(text or ""), flags=re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    @classmethod
    def _sanitize_output(cls, text: str) -> str:
        cleaned = (text or "").strip().replace("`", "").strip()
        lowered = cleaned.lower()
        if lowered in _INVALID_SHORT_OUTPUTS:
            return ""
        return cleaned

    @classmethod
    def _extract_text_from_raw(cls, raw: dict) -> tuple[str, str]:
        choices = raw.get("choices") if isinstance(raw, dict) else None
        if not (isinstance(choices, list) and choices):
            return "", "none"
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        if not isinstance(message, dict):
            return "", "none"

        content = str(message.get("content", "") or "").strip()
        final = cls._extract_final_tag(content)
        if final:
            return cls._sanitize_output(final), "final_tag"
        if content:
            return cls._sanitize_output(content), "content"

        reasoning = str(message.get("reasoning_content", "") or "").strip()
        final = cls._extract_final_tag(reasoning)
        if final:
            return cls._sanitize_output(final), "reasoning_final_tag"
        if reasoning:
            return cls._sanitize_output(reasoning), "reasoning_content"
        return "", "none"

    @staticmethod
    def _is_invalid_output(text: str) -> bool:
        normalized = (text or "").strip().lower()
        return (not normalized) or len(normalized) <= 2 or normalized in _INVALID_SHORT_OUTPUTS

    def _post_chat(self, payload: dict) -> dict:
        req = urllib.request.Request(
            DEFAULT_OPENAI_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        attempt = 0
        max_attempts = 2
        while True:
            attempt += 1
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code == HTTPStatus.TOO_MANY_REQUESTS and attempt < max_attempts:
                    retry_after = self._retry_after_seconds(exc)
                    if retry_after is not None and 0 < retry_after <= 5:
                        time.sleep(retry_after)
                        continue

                if exc.code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                    raise MissingAPIKeyError("Chave da OpenAI inválida ou ausente") from exc
                if exc.code == HTTPStatus.NOT_FOUND:
                    raise ModelNotFoundError("Modelo da OpenAI não encontrado") from exc
                if exc.code == HTTPStatus.TOO_MANY_REQUESTS:
                    raise RateLimitError(self._build_rate_limit_message(exc)) from exc
                raise AIWritingError(f"Falha na API da OpenAI (HTTP {exc.code})") from exc
            except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                raise AIRequestTimeoutError("Timeout na API da OpenAI") from exc

    def suggest(self, input_text: str, instruction: str, context: Optional[dict] = None) -> str:
        if not self.api_key:
            raise MissingAPIKeyError("Chave da OpenAI não configurada")

        prompt = self.build_prompt(input_text, instruction, context)
        system_prompt = "Você é um assistente que reescreve textos corporativos em português do Brasil."
        debug = bool((context or {}).get("debug_log_text"))

        for generation_attempt in range(2):
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": self.temperature + (0.1 if generation_attempt == 1 else 0.0),
                "max_tokens": self.max_new_tokens,
            }
            if self.top_p is not None:
                payload["top_p"] = float(self.top_p)

            raw = self._post_chat(payload)
            text, used_field = self._extract_text_from_raw(raw)
            if debug:
                print(
                    f"[AI][openai] model={self.model} temp={payload['temperature']} top_p={payload.get('top_p')} "
                    f"max_tokens={self.max_new_tokens} source={used_field} output={text!r}"
                )
            if not self._is_invalid_output(text):
                return text

            system_prompt = (
                "Você é um revisor de texto em pt-BR. Corrija ortografia e digitação agressivamente quando necessário. "
                "Retorne somente o texto final útil, evitando respostas vazias ou tokens soltos."
            )

        raise AIWritingError("A IA não retornou texto útil. Tente novamente em instantes.")

    @staticmethod
    def _retry_after_seconds(exc: urllib.error.HTTPError) -> Optional[float]:
        value = exc.headers.get("Retry-After") if exc.headers else None
        if not value:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _build_rate_limit_message(exc: urllib.error.HTTPError) -> str:
        default = "Limite de requisições da OpenAI atingido"
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            return default

        error = payload.get("error") if isinstance(payload, dict) else None
        code = str(error.get("code", "")) if isinstance(error, dict) else ""
        message = str(error.get("message", "")) if isinstance(error, dict) else ""
        text = f"{code} {message}".lower()
        if "insufficient_quota" in text or "quota" in text:
            return "Cota da OpenAI esgotada. Verifique faturamento e limites da conta."
        return default

    def check_connectivity(self) -> None:
        req = urllib.request.Request(
            DEFAULT_CONNECTIVITY_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout):
                return
        except urllib.error.HTTPError as exc:
            if exc.code in {HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN}:
                raise MissingAPIKeyError("Chave da OpenAI inválida ou ausente") from exc
            raise AIWritingError(f"Falha ao validar conectividade OpenAI (HTTP {exc.code})") from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise AIRequestTimeoutError("Timeout na API da OpenAI") from exc
