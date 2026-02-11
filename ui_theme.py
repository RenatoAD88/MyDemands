from __future__ import annotations

from typing import Tuple

APP_STYLESHEET = """
QWidget { font-size: 13px; }
QMainWindow { background: #ffffff; }
QTabWidget::pane { border: 1px solid #d4d9e2; background: #000000; }
QTabBar::tab { background: #e9edf5; padding: 8px 14px; margin-right: 2px; }
QTabBar::tab:selected { background: #000000; font-weight: 600; }
QPushButton { background: #e7ebf4; border: 1px solid #c8d0df; border-radius: 6px; padding: 6px 12px; }
QPushButton#primaryAction { background: #1e6fff; color: #000000; border: 1px solid #ffffff; font-weight: 600; }
QPushButton#dangerAction { background: #ffe8e8; color: #9b1c1c; border: 1px solid #ffffff; }
QLineEdit, QTextEdit, QComboBox, QDateEdit, QListWidget { background: #000000; border: 1px solid #000000; border-radius: 6px; padding: 4px; }
QTableWidget { gridline-color: #e6ebf5; alternate-background-color: #f8faff; }
QHeaderView::section { background: #edf2fa; border: none; border-bottom: 1px solid #d4d9e2; padding: 6px; font-weight: 600; }
QLabel#errorText { color: #b42318; }
"""


def status_color(status: str) -> Tuple[int, int, int]:
    s = (status or "").strip().lower()
    if s == "concluído" or s == "concluido":
        return (210, 242, 220)
    if s == "em espera":
        return (255, 243, 205)
    if s == "cancelado":
        return (238, 238, 238)
    return (230, 239, 255)


def timing_color(timing: str) -> Tuple[int, int, int]:
    t = (timing or "").strip().lower()
    if "atras" in t:
        return (255, 228, 230)
    if "sem prazo" in t:
        return (243, 244, 246)
    if "dentro" in t or "no prazo" in t:
        return (220, 252, 231)
    if "conclu" in t:
        return (224, 231, 255)
    return (243, 244, 246)
