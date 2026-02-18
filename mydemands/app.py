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
from mydemands.services.bootstrap_flow import resolve_startup_decision
from mydemands.services.user_context import UserContext, set_current_user
from mydemands.ui.dialogs.confirm_remember_dialog import ConfirmRememberDialog
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

    def _open_main(email: str):
        user = users.get_by_email(email)
        if user is None:
            return
        paths.migrate_legacy_data_for_user(email)
        user_dir = paths.ensure_user_dirs(email)
        context = UserContext(email=user.email, role=user.role, user_id=paths.user_id_from_email(user.email), user_dir=user_dir)
        set_current_user(context)
        store = CsvStore(str(paths.user_data_dir(email)))
        win = MainWindow(
            store,
            logged_user_email=email,
            logged_user_role=user.role,
            email_service=email_service,
            backup_root=str(user_dir / "backups"),
            exports_root=str(user_dir / "exports"),
            on_logoff=lambda: (auth.logout(), set_current_user(None), qt_app.quit()),
        )
        win.resize(1280, 720)
        win.show()
        qt_app._main_win = win  # type: ignore[attr-defined]

    startup = resolve_startup_decision(auth)
    if startup.state == "confirm_remember" and startup.user_email:
        confirm = ConfirmRememberDialog(startup.user_email)
        result = confirm.exec()
        if result == ConfirmRememberDialog.Accepted and confirm.choice == "continue":
            _open_main(startup.user_email)
        elif confirm.choice == "switch":
            auth.logout()
            login = LoginWindow(auth, reset_service, _open_main)
            if login.exec() != LoginWindow.Accepted:
                return 0
        else:
            return 0
    else:
        login = LoginWindow(auth, reset_service, _open_main)
        if login.exec() != LoginWindow.Accepted:
            return 0

    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
