from __future__ import annotations

from mydemands.domain.models import EmailSettings
from mydemands.infra.email.email_provider import IEmailProvider
from mydemands.infra.email.smtp_provider import SmtpEmailProvider
from mydemands.infra.repositories.settings_repository import SettingsRepository
from mydemands.infra.secrets.secret_store import ISecretStore

SMTP_PASSWORD_KEY = "smtp_password"
DEFAULT_RECOVERY_SUBJECT = "MyDemands - Recuperação de senha"
PROVISIONAL_MINUTES = 15


class EmailService:
    def __init__(
        self,
        settings_repository: SettingsRepository,
        secret_store: ISecretStore,
        provider: IEmailProvider | None = None,
    ):
        self.settings_repository = settings_repository
        self.secret_store = secret_store
        self._provider = provider

    def load_settings(self) -> EmailSettings | None:
        return self.settings_repository.load_email_settings()


    @staticmethod
    def validate_recovery_template(body_template: str) -> None:
        if "{PASSWORD}" not in body_template:
            raise ValueError("Body deve conter {PASSWORD}")
        if "{MINUTOS}" not in body_template:
            raise ValueError("Body deve conter {MINUTOS}")
        if "spam" not in body_template.lower():
            raise ValueError("Body deve orientar verificação de spam")

    @staticmethod
    def render_recovery_body(body_template: str, provisional_password: str) -> str:
        rendered = body_template.replace("{PASSWORD}", provisional_password).replace("{MINUTOS}", str(PROVISIONAL_MINUTES))
        if "{PASSWORD}" in rendered or "{MINUTOS}" in rendered:
            raise ValueError("Template de recuperação inválido")
        return rendered

    def get_provider(self) -> IEmailProvider:
        if self._provider:
            return self._provider
        settings = self.settings_repository.load_email_settings()
        if not settings:
            raise RuntimeError("SMTP_NOT_CONFIGURED")
        secret = self.secret_store.get(SMTP_PASSWORD_KEY)
        if not secret:
            raise RuntimeError("SMTP_NOT_CONFIGURED")
        return SmtpEmailProvider(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=secret.decode("utf-8"),
            use_tls=settings.use_tls,
        )

    def send_recovery_email(self, to_email: str, provisional_password: str) -> None:
        settings = self.settings_repository.load_email_settings()
        if not settings:
            raise RuntimeError("SMTP_NOT_CONFIGURED")
        self.validate_recovery_template(settings.body_template)
        body = self.render_recovery_body(settings.body_template, provisional_password)
        subject = settings.subject_template or DEFAULT_RECOVERY_SUBJECT
        self.get_provider().send(
            to_email=to_email,
            from_email=settings.from_email,
            subject=subject,
            body=body,
            reply_to=settings.reply_to,
        )

    def send_test_email(self, to_email: str) -> None:
        settings = self.settings_repository.load_email_settings()
        if not settings:
            raise RuntimeError("SMTP_NOT_CONFIGURED")
        body = "Teste de envio MyDemands. Verifique também a caixa de spam."
        self.get_provider().send(
            to_email=to_email,
            from_email=settings.from_email,
            subject="Teste SMTP MyDemands",
            body=body,
            reply_to=settings.reply_to,
        )
