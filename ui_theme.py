from __future__ import annotations

from typing import Tuple

APP_STYLESHEET = """
QWidget { font-size: 13px; color: #000000; }
QMainWindow { background: #f4f4f4; }
QTabWidget::pane { border: 1px solid #000000; background: #ffffff; }
QTabBar::tab { background: #e6e6e6; color: #000000; border: 1px solid #000000; padding: 8px 14px; margin-right: 2px; }
QTabBar::tab:selected { background: #ffffff; color: #000000; font-weight: 600; }
QPushButton { background: #efefef; color: #000000; border: 1px solid #000000; border-radius: 0px; padding: 6px 12px; }
QPushButton#primaryAction { background: #d9d9d9; color: #000000; border: 1px solid #000000; font-weight: 600; }
QPushButton#dangerAction { background: #f2dede; color: #000000; border: 1px solid #000000; }
QLineEdit, QTextEdit, QComboBox, QDateEdit, QListWidget { background: #ffffff; color: #000000; border: 1px solid #000000; border-radius: 0px; padding: 4px; }
QTableWidget { color: #000000; gridline-color: #000000; alternate-background-color: #f7f7f7; border: 1px solid #000000; }
QHeaderView::section { background: #e6e6e6; color: #000000; border: 1px solid #000000; padding: 6px; font-weight: 600; }
QGroupBox { color: #000000; border: 1px solid #000000; margin-top: 8px; padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px 0 4px; }
QLabel#errorText { color: #000000; }
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
