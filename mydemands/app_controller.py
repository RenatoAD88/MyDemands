from __future__ import annotations

import logging
from typing import Any

from mydemands.services.auth_service import AuthService
from mydemands.services.user_context import clear


logger = logging.getLogger(__name__)


class AppController:
    def __init__(self, auth_service: AuthService, qt_app: Any, login_factory):
        self.auth_service = auth_service
        self.qt_app = qt_app
        self.login_factory = login_factory
        self._main_window: Any | None = None
        self._login_window: Any | None = None

    def register_main_window(self, main_window: Any) -> None:
        self._main_window = main_window

    def _show_login_window(self) -> None:
        if self._login_window is not None:
            self._login_window.close()
            self._login_window.deleteLater()
        login = self.login_factory()
        self._login_window = login
        login.show()
        login.raise_()
        login.activateWindow()
        if hasattr(login, "focus_first_field"):
            login.focus_first_field()

    def handle_logoff(self) -> None:
        main_window = self._main_window
        if main_window is None:
            main_window = getattr(self.qt_app, "_main_win", None)

        if main_window is not None:
            try:
                main_window.save_backup_for_logoff()
            except Exception as exc:  # pragma: no cover - defensive UI path
                logger.exception("Falha ao gerar backup no logoff")
                try:
                    from PySide6.QtWidgets import QMessageBox

                    QMessageBox.warning(
                        main_window,
                        "Falha no backup",
                        f"Não foi possível gerar o backup automático no logoff.\n\n{exc}",
                    )
                except Exception:
                    logger.exception("Falha ao exibir aviso de backup")

        self.auth_service.logout()
        clear()
        self._close_open_modal()

        if main_window is not None:
            if hasattr(main_window, "prepare_for_logoff"):
                main_window.prepare_for_logoff()
            main_window.close()
            main_window.deleteLater()
            self._main_window = None
            if getattr(self.qt_app, "_main_win", None) is main_window:
                self.qt_app._main_win = None

        self._show_login_window()

    def _close_open_modal(self) -> None:
        active_modal_getter = getattr(self.qt_app, "activeModalWidget", None)
        if not callable(active_modal_getter):
            return
        active_modal = active_modal_getter()
        if active_modal is None:
            return
        try:
            active_modal.reject()
        except Exception:
            active_modal.close()
