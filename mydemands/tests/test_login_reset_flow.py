from pathlib import Path

import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from mydemands.domain.models import EmailSettings
from mydemands.infra.repositories.last_login_repository import LastLoginRepository
from mydemands.infra.repositories.user_prefs_repository import UserPrefsRepository
from mydemands.services.email_service import SMTP_PASSWORD_KEY
from mydemands.ui.login_window import LoginWindow

QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog


def _get_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


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
            body_template="Senha provisória: {PASSWORD}. Verifique spam.",
        )
    )
    env["secrets"].set(SMTP_PASSWORD_KEY, b"secret")


def test_login_with_provisional_password_requires_reset_modal(env, monkeypatch):
    _get_app()
    env["auth"].register("user@test.com", "Abcdef1!")
    _configure(env)
    monkeypatch.setattr(env["reset"], "_generate_provisional_password", lambda: "Prov_1234567890")
    env["reset"].request_password_reset("user@test.com")

    paths = env["paths"]
    prefs_repo = UserPrefsRepository(paths)
    last_login = LastLoginRepository(paths.base_dir / "last_login.json")

    opened = {"reset_modal": False, "email": None}

    class _FakeResetDialog:
        def __init__(self, auth_service, email, parent=None):
            opened["reset_modal"] = True
            self.final_password = "Xyzabc1!"

        def exec(self):
            return QDialog.Accepted

    monkeypatch.setattr("mydemands.ui.login_window.ResetPasswordDialog", _FakeResetDialog)

    login = LoginWindow(env["auth"], env["reset"], lambda email: opened.__setitem__("email", email), prefs_repo, last_login)
    login.email.setText("user@test.com")
    login.password.setText("Prov_1234567890")
    login._login()

    assert opened["reset_modal"] is True
    assert opened["email"] == "user@test.com"


def test_loginwindow_clickable_label_opens_forgot_password(env, monkeypatch):
    _get_app()
    paths = env["paths"]
    prefs_repo = UserPrefsRepository(paths)
    last_login = LastLoginRepository(paths.base_dir / "last_login.json")
    opened = {"called": False}

    class _FakeForgotDialog:
        def __init__(self, reset_service, parent=None):
            opened["called"] = True

        def exec(self):
            return QDialog.Accepted

    monkeypatch.setattr("mydemands.ui.login_window.ForgotPasswordDialog", _FakeForgotDialog)

    login = LoginWindow(env["auth"], env["reset"], lambda _email: None, prefs_repo, last_login)
    login.forgot_label.clicked.emit()
    assert opened["called"] is True
