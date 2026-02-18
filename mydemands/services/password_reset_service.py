from __future__ import annotations

import random
from collections import defaultdict
from datetime import datetime, timedelta

from mydemands.domain.password_policy import PasswordPolicy
from mydemands.infra.repositories.user_repository import UserRepository
from mydemands.services.auth_service import hash_password
from mydemands.services.email_service import EmailService


class PasswordResetError(Exception):
    pass


class PasswordResetService:
    NEUTRAL_MESSAGE = "Se houver conta com este e-mail, enviaremos instruções. Verifique a caixa de spam."

    def __init__(self, users: UserRepository, email_service: EmailService):
        self.users = users
        self.email_service = email_service
        self._requests_by_email: dict[str, list[datetime]] = defaultdict(list)

    @staticmethod
    def _norm(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _generate_provisional_password() -> str:
        return "Prov_" + "".join(str(random.randint(0, 9)) for _ in range(10))

    def request_password_reset(self, email: str) -> str:
        normalized = self._norm(email)
        now = datetime.utcnow()
        requests = [t for t in self._requests_by_email[normalized] if (now - t) <= timedelta(hours=1)]
        self._requests_by_email[normalized] = requests
        if len(requests) >= 5:
            return self.NEUTRAL_MESSAGE

        settings = self.email_service.load_settings()
        if not settings or self.email_service.secret_store.get("smtp_password") is None:
            raise RuntimeError("SMTP_NOT_CONFIGURED")

        self._requests_by_email[normalized].append(now)
        user = self.users.get_by_email(normalized)
        if not user:
            return self.NEUTRAL_MESSAGE

        provisional_password = self._generate_provisional_password()
        user.password_hash = hash_password(provisional_password)
        user.must_change_password = True
        self.users.update(user)

        self.email_service.send_recovery_email(normalized, provisional_password)
        return self.NEUTRAL_MESSAGE

    def save_final_password(self, email: str, new_password: str) -> None:
        normalized = self._norm(email)
        ok, errors = PasswordPolicy.validate(new_password)
        if not ok:
            raise PasswordResetError("; ".join(errors))

        user = self.users.get_by_email(normalized)
        if not user:
            raise PasswordResetError("Usuário não encontrado")

        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        self.users.update(user)
