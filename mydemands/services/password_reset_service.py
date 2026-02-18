from __future__ import annotations

import hashlib
import random
import re
from datetime import datetime, timedelta

from mydemands.domain.password_policy import PasswordPolicy
from mydemands.infra.repositories.token_repository import ResetTokenRepository
from mydemands.infra.repositories.user_repository import UserRepository
from mydemands.services.auth_service import hash_password
from mydemands.services.email_service import EmailService

APP_PEPPER = "mydemands_local_pepper_v1"


class PasswordResetError(Exception):
    pass


class PasswordResetService:
    def __init__(self, users: UserRepository, tokens: ResetTokenRepository, email_service: EmailService):
        self.users = users
        self.tokens = tokens
        self.email_service = email_service
        self._last_requests: dict[str, datetime] = {}

    @staticmethod
    def _norm(email: str) -> str:
        return email.strip().lower()

    def _hash_token(self, email: str, token: str) -> str:
        normalized = self._norm(email)
        return hashlib.sha256(f"{token}{normalized}{APP_PEPPER}".encode("utf-8")).hexdigest()

    def request_reset(self, email: str) -> str | None:
        normalized = self._norm(email)
        now = datetime.utcnow()
        last = self._last_requests.get(normalized)
        if last and (now - last).total_seconds() < 30:
            return None
        settings = self.email_service.load_settings()
        if not settings or self.email_service.secret_store.get("smtp_password") is None:
            raise RuntimeError("SMTP_NOT_CONFIGURED")
        self._last_requests[normalized] = now
        user = self.users.get_by_email(normalized)
        if not user:
            return None
        token = "Prov_" + "".join(str(random.randint(0, 9)) for _ in range(10))
        token_hash = self._hash_token(normalized, token)
        self.tokens.add(normalized, token_hash, now + timedelta(minutes=15), used=0)
        self.email_service.send_recovery_email(normalized, token, 15)
        return token

    def confirm_reset(self, email: str, token: str, new_password: str) -> None:
        normalized = self._norm(email)
        if not re.match(r"^Prov_\d{10}$", token or ""):
            raise PasswordResetError("Token inválido")
        ok, errors = PasswordPolicy.validate(new_password)
        if not ok:
            raise PasswordResetError("; ".join(errors))
        token_hash = self._hash_token(normalized, token)
        row = self.tokens.get_valid(normalized, token_hash, datetime.utcnow())
        if not row:
            raise PasswordResetError("Token inválido ou expirado")
        user = self.users.get_by_email(normalized)
        if not user:
            raise PasswordResetError("Usuário não encontrado")
        user.password_hash = hash_password(new_password)
        self.users.update(user)
        self.tokens.mark_used(normalized, token_hash)
