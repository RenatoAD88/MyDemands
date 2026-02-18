from mydemands.domain.models import EmailSettings
from mydemands.services.email_service import EmailService, SMTP_PASSWORD_KEY


def _settings(host: str = "smtp.test") -> EmailSettings:
    return EmailSettings(
        smtp_host=host,
        smtp_port=587,
        use_tls=True,
        smtp_username="user",
        from_email="noreply@test.com",
        reply_to=None,
        subject_template="Recuperação",
        body_template="Senha provisória: {PASSWORD}. Expira em {MINUTOS} minutos. Verifique spam.",
    )


def test_secret_store_save_and_load_smtp_password(env):
    email_service: EmailService = env["email"]
    email_service.save_smtp_settings(_settings(), smtp_password="app-secret")

    loaded_password = email_service.get_smtp_password_for_send()
    email_service.send_test_email("master@test.com")

    assert loaded_password == "app-secret"
    assert env["secrets"].get(SMTP_PASSWORD_KEY) == b"app-secret"
    assert len(env["provider"].calls) == 1


def test_smtp_password_not_overwritten_when_field_empty(env):
    email_service: EmailService = env["email"]
    email_service.save_smtp_settings(_settings(), smtp_password="senha-a")

    email_service.save_smtp_settings(_settings(host="smtp.changed"), smtp_password=None)

    assert email_service.get_smtp_password_for_send() == "senha-a"


def test_test_send_uses_ui_values_without_saving(env):
    email_service: EmailService = env["email"]
    email_service.save_smtp_settings(_settings(host="smtp.saved"), smtp_password="saved")

    temp_settings = _settings(host="smtp.unsaved")
    email_service.send_test_email(
        "master@test.com",
        settings_override=temp_settings,
        smtp_password_override="unsaved-secret",
    )

    assert len(env["provider"].calls) == 1
    loaded = email_service.load_settings()
    assert loaded is not None
    assert loaded.smtp_host == "smtp.saved"


def test_test_send_uses_ui_password_if_provided_else_secret(env):
    email_service: EmailService = env["email"]
    email_service.save_smtp_settings(_settings(), smtp_password="persisted")

    email_service.send_test_email("master@test.com", settings_override=_settings(), smtp_password_override="ui-value")
    assert len(env["provider"].calls) == 1

    email_service.send_test_email("master@test.com", settings_override=_settings())
    assert len(env["provider"].calls) == 2
