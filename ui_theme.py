from __future__ import annotations

from typing import Tuple

APP_STYLESHEET = """
QWidget { font-size: 13px; color: #1f2937; }
QMainWindow { background: #f3f6fb; }

QTabWidget::pane {
    border: 1px solid #c7d4ea;
    background: #ffffff;
}
QTabBar::tab {
    background: #e8eef9;
    color: #334155;
    border: 1px solid #c7d4ea;
    padding: 8px 14px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #7aa2e3;
    font-weight: 600;
}

QPushButton {
    background: #eef2fa;
    color: #1f2937;
    border: 1px solid #bccae3;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton#primaryAction {
    background: #2f6fe4;
    color: #ffffff;
    border: 1px solid #1f5bca;
    font-weight: 600;
}
QPushButton#dangerAction {
    background: #fdecec;
    color: #9f1f1f;
    border: 1px solid #efb1b1;
}

QLineEdit, QTextEdit, QComboBox, QDateEdit, QListWidget {
    background: #ffffff;
    color: #111827;
    border: 1px solid #bccae3;
    border-radius: 6px;
    padding: 4px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QListWidget:focus {
    border: 1px solid #2f6fe4;
}

QTableWidget {
    background: #ffffff;
    color: #111827;
    gridline-color: #d7e0ef;
    alternate-background-color: #f8fbff;
    border: 1px solid #c7d4ea;
}
QHeaderView::section {
    background: #dde7f8;
    color: #1e293b;
    border: none;
    border-bottom: 1px solid #c7d4ea;
    padding: 6px;
    font-weight: 600;
}

QGroupBox {
    color: #1e293b;
    border: 1px solid #c7d4ea;
    border-radius: 8px;
    margin-top: 8px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px 0 4px;
}

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
