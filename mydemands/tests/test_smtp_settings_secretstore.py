from mydemands.domain.models import EmailSettings
from mydemands.services.email_service import SMTP_PASSWORD_KEY


def test_save_settings_and_secret_separated(env):
    env["settings"].save_email_settings(
        EmailSettings(
            smtp_host="smtp.test",
            smtp_port=587,
            use_tls=True,
            smtp_username="user",
            from_email="noreply@test.com",
            reply_to="reply@test.com",
            subject_template="Recuperação",
            body_template="Use {PASSWORD}. Expira em {MINUTOS} minutos. Verifique spam.",
        )
    )
    env["secrets"].set(SMTP_PASSWORD_KEY, b"app-secret")

    raw = env["paths"].email_settings_file.read_text(encoding="utf-8")
    assert "app-secret" not in raw

    loaded = env["settings"].load_email_settings()
    assert loaded is not None
    assert loaded.smtp_host == "smtp.test"
    assert env["secrets"].get(SMTP_PASSWORD_KEY) == b"app-secret"
