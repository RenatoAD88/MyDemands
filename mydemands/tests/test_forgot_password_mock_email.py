from mydemands.domain.models import EmailSettings
from mydemands.services.email_service import SMTP_PASSWORD_KEY


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


def test_request_reset_gera_token_salva_hash_e_envia(env):
    env["auth"].register("user@test.com", "Abcdef1!")
    _configure(env)

    token = env["reset"].request_reset("user@test.com")

    assert token.startswith("Prov_")
    assert len(token) == 15
    with env["db"].connect() as conn:
        row = conn.execute("SELECT * FROM reset_tokens WHERE email = ?", ("user@test.com",)).fetchone()
    assert row is not None
    assert row["used"] == 0

    calls = env["provider"].calls
    assert len(calls) == 1
    payload = calls[0]
    assert payload["subject"] == "Recuperação"
    assert "spam" in payload["body"].lower()
    assert token in payload["body"]
