from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QApplication

from ui_theme import APP_STYLESHEET

LIGHT_THEME = APP_STYLESHEET
DARK_THEME = """
QWidget { font-size: 13px; color: #e5e7eb; background: #111827; }
QMainWindow { background: #111827; }
QDialog { background: #111827; }
QLabel { color: #e5e7eb; }
QPushButton { background: #1f2937; color: #f9fafb; border: 1px solid #374151; border-radius: 6px; padding: 6px 12px; }
QLineEdit, QTextEdit, QComboBox, QDateEdit, QListWidget, QTableWidget { background: #1f2937; color: #f9fafb; border: 1px solid #374151; }
QHeaderView::section { background: #374151; color: #f3f4f6; }
"""


class ThemeService:
    def __init__(self, app: QApplication):
        self.app = app
        self._current = "light"
        self._listeners: list[Callable[[str], None]] = []

    def add_theme_listener(self, callback: Callable[[str], None]) -> None:
        self._listeners.append(callback)

    def apply_theme(self, theme_name: str) -> None:
        theme = (theme_name or "light").strip().lower()
        if theme not in {"light", "dark"}:
            theme = "light"
        stylesheet = DARK_THEME if theme == "dark" else LIGHT_THEME
        self.app.setStyleSheet(stylesheet)
        self._current = theme
        for callback in list(self._listeners):
            callback(theme)

    def current_theme(self) -> str:
        return self._current
