from __future__ import annotations

from typing import Any

from mydemands.services.auth_service import AuthService
from mydemands.services.user_context import clear


class AppController:
    def __init__(self, auth_service: AuthService, qt_app: Any):
        self.auth_service = auth_service
        self.qt_app = qt_app

    def logoff_and_exit(self) -> None:
        self.auth_service.logout()
        clear()
        for win in list(self.qt_app.topLevelWidgets()):
            win.close()
        self.qt_app.quit()
