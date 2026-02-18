import pytest

from mydemands.services.email_service import EmailService


def test_template_validation_requires_password_minutes_and_spam():
    with pytest.raises(ValueError, match="\\{PASSWORD\\}"):
        EmailService.validate_recovery_template("Expira em {MINUTOS} minutos. Verifique spam.")

    with pytest.raises(ValueError, match="\\{MINUTOS\\}"):
        EmailService.validate_recovery_template("Senha: {PASSWORD}. Verifique spam.")

    with pytest.raises(ValueError, match="spam"):
        EmailService.validate_recovery_template("Senha: {PASSWORD}. Expira em {MINUTOS} minutos.")
