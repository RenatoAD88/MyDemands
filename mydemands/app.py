from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app import MainWindow
from csv_store import CsvStore
from ui_theme import APP_STYLESHEET
from mydemands.infra.db import Database
from mydemands.infra.paths import Paths
from mydemands.infra.repositories.session_repository import SessionRepository
from mydemands.infra.repositories.settings_repository import SettingsRepository
from mydemands.infra.repositories.token_repository import ResetTokenRepository
from mydemands.infra.repositories.user_repository import UserRepository
from mydemands.infra.secrets.dpapi_secret_store import WindowsDpapiSecretStore
from mydemands.services.auth_service import AuthService
from mydemands.services.email_service import EmailService
from mydemands.services.password_reset_service import PasswordResetService
from mydemands.ui.login_window import LoginWindow


def main() -> int:
    qt_app = QApplication(sys.argv)
    qt_app.setStyleSheet(APP_STYLESHEET)

    paths = Paths()
    paths.ensure_base_dir()
    db = Database(paths)
    db.init_db()

    users = UserRepository(db)
    sessions = SessionRepository(paths.session_file)
    settings = SettingsRepository(paths.email_settings_file)
    secrets_store = WindowsDpapiSecretStore(paths.secrets_file)
    auth = AuthService(users, sessions, secrets_store)
    auth.seed_master()

    email_service = EmailService(settings, secrets_store)
    token_repo = ResetTokenRepository(db)
    reset_service = PasswordResetService(users, token_repo, email_service)

    user = auth.try_auto_login()

    def _open_main(email: str):
        store = CsvStore(str(paths.base_dir))
        win = MainWindow(store, logged_user_email=email, logged_user_role=users.get_by_email(email).role if users.get_by_email(email) else "default", email_service=email_service)
        win.resize(1280, 720)
        win.show()
        qt_app._main_win = win  # type: ignore[attr-defined]

    if user:
        _open_main(user.email)
    else:
        login = LoginWindow(auth, reset_service, _open_main)
        if login.exec() != LoginWindow.Accepted:
            return 0

    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
