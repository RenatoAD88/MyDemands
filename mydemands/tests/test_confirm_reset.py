from datetime import datetime, timedelta

import pytest

from mydemands.domain.models import EmailSettings
from mydemands.services.email_service import SMTP_PASSWORD_KEY
from mydemands.services.password_reset_service import PasswordResetError


def _configure(env):
    env["settings"].save_email_settings(
        EmailSettings(
            smtp_host="smtp.test",
            smtp_port=587,
            use_tls=True,
            smtp_username="user",
            from_email="noreply@test.com",
            reply_to=None,
            subject_template="Recuperação",
            body_template="Seu token é {TOKEN}. Expira em {MINUTOS} minutos. Verifique spam.",
        )
    )
    env["secrets"].set(SMTP_PASSWORD_KEY, b"secret")


def test_confirm_reset_token_valido(env):
    env["auth"].register("user@test.com", "Abcdef1!")
    _configure(env)
    token = env["reset"].request_reset("user@test.com")

    env["reset"].confirm_reset("user@test.com", token, "Xyzabc1!")

    with env["db"].connect() as conn:
        row = conn.execute("SELECT used FROM reset_tokens WHERE email = ?", ("user@test.com",)).fetchone()
    assert row["used"] == 1
    assert env["auth"].authenticate("user@test.com", "Xyzabc1!")


def test_confirm_reset_expirado_falha(env):
    env["auth"].register("user@test.com", "Abcdef1!")
    _configure(env)
    token = "Prov_1234567890"
    token_hash = env["reset"]._hash_token("user@test.com", token)
    env["tokens"].add("user@test.com", token_hash, datetime.utcnow() - timedelta(minutes=1), used=0)

    with pytest.raises(PasswordResetError):
        env["reset"].confirm_reset("user@test.com", token, "Xyzabc1!")


def test_confirm_reset_token_usado_falha(env):
    env["auth"].register("user@test.com", "Abcdef1!")
    _configure(env)
    token = "Prov_1234567890"
    token_hash = env["reset"]._hash_token("user@test.com", token)
    env["tokens"].add("user@test.com", token_hash, datetime.utcnow() + timedelta(minutes=15), used=1)

    with pytest.raises(PasswordResetError):
        env["reset"].confirm_reset("user@test.com", token, "Xyzabc1!")
