from mydemands.services.email_service import EmailService


def test_migrate_token_to_password_template():
    legacy = "Código provisório: {TOKEN}. Verifique spam."

    migrated = EmailService.migrate_legacy_recovery_template(legacy)

    assert "{PASSWORD}" in migrated
    assert "{TOKEN}" not in migrated
    assert "Senha provisória" in migrated
    assert "{MINUTOS}" in migrated


def test_migrate_empty_template_uses_default():
    migrated = EmailService.migrate_legacy_recovery_template("")

    assert "{PASSWORD}" in migrated
    assert "{MINUTOS}" in migrated
    assert "spam" in migrated.lower()
