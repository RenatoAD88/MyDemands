from mydemands.domain.models import EmailSettings
from mydemands.services.auth_service import verify_password
from mydemands.services.email_service import SMTP_PASSWORD_KEY
from mydemands.services.master_password_admin_service import MasterPasswordAdminService


def _configure_smtp(env):
    env["settings"].save_email_settings(
        EmailSettings(
            smtp_host="smtp.test",
            smtp_port=587,
            use_tls=True,
            smtp_username="user",
            from_email="noreply@test.com",
            reply_to=None,
            subject_template="Recuperação",
            body_template="Senha provisória: {PASSWORD}. Expira em {MINUTOS} minutos. Verifique spam.",
        )
    )
    env["secrets"].set(SMTP_PASSWORD_KEY, b"secret")


def test_list_users_returns_all_emails(env):
    env["auth"].register("a@test.com", "Abcdef1!")
    env["auth"].register("b@test.com", "Abcdef1!")
    service = MasterPasswordAdminService(env["users"], env["email"], env["reset"])

    emails = [u.email for u in service.list_users()]

    assert emails == ["a@test.com", "b@test.com"]


def test_send_new_password_updates_user_and_calls_email_provider(env, monkeypatch):
    env["auth"].register("user@test.com", "Abcdef1!")
    _configure_smtp(env)
    service = MasterPasswordAdminService(env["users"], env["email"], env["reset"])

    monkeypatch.setattr(env["reset"], "_generate_provisional_password", lambda: "Prov_1234567890")

    service.send_new_password("user@test.com")

    user = env["users"].get_by_email("user@test.com")
    assert user is not None
    assert user.must_change_password is True
    assert verify_password("Prov_1234567890", user.password_hash)
    assert user.provisional_expires_at is not None
    assert len(env["provider"].calls) == 1


def test_send_new_password_requires_smtp_config(env):
    env["auth"].register("user@test.com", "Abcdef1!")
    service = MasterPasswordAdminService(env["users"], env["email"], env["reset"])

    try:
        service.send_new_password("user@test.com")
    except RuntimeError as exc:
        assert str(exc) == "SMTP_NOT_CONFIGURED"
    else:
        raise AssertionError("Esperava erro de SMTP não configurado")
