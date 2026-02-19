from __future__ import annotations

BASE_QSS = """
QWidget {
    font-size: 13px;
}

QTabBar::tab {
    border: 1px solid;
    padding: 8px 14px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    border: 1px solid;
    font-weight: 600;
}

QPushButton {
    border: 1px solid;
    border-radius: 6px;
    padding: 6px 12px;
}
QToolButton[toolbarAction="true"] {
    border: 1px solid;
    border-radius: 8px;
    padding: 6px;
    min-height: 28px;
    min-width: 28px;
}
QToolButton[toolbarAction="true"]:hover {
    border: 1px solid;
}
QToolButton[toolbarAction="true"]::menu-indicator {
    image: none;
}
QToolButton[infoIconAction="true"] {
    border: none;
    padding: 0;
    min-width: 28px;
    min-height: 28px;
}
QToolButton[infoIconAction="true"]:hover {
    border-radius: 14px;
}

QLineEdit, QTextEdit, QComboBox, QDateEdit, QListWidget {
    border: 1px solid;
    border-radius: 6px;
    padding: 4px;
}
QComboBox, QDateEdit {
    min-height: 26px;
    padding-top: 3px;
    padding-bottom: 3px;
}
QDateEdit {
    min-width: 130px;
}
QComboBox::drop-down, QDateEdit::drop-down {
    width: 22px;
    border-left: 1px solid;
}
QComboBox::down-arrow, QDateEdit::down-arrow {
    margin-right: 6px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QListWidget:focus {
    border: 1px solid;
}
QComboBox QAbstractItemView {
    border: 1px solid;
    outline: 0;
}
QComboBox QAbstractItemView::item {
    min-height: 24px;
    padding: 4px 8px;
}

QTableWidget {
    border: 1px solid;
}
QHeaderView::section {
    border: none;
    border-bottom: 1px solid;
    padding: 6px;
    font-weight: 600;
}

QGroupBox {
    border: 1px solid;
    border-radius: 8px;
    margin-top: 8px;
    padding-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px 0 4px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid;
    border-radius: 3px;
}
QCheckBox::indicator:unchecked:hover {
    border: 1px solid;
}
QCheckBox::indicator:checked {
    border: 1px solid;
    image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><path d='M3.2 8.4 6.6 11.8 12.8 4.8' fill='none' stroke='%23ffffff' stroke-width='2.3' stroke-linecap='round' stroke-linejoin='round'/></svg>");
}
QCheckBox::indicator:disabled {
    border: 1px solid;
}
QCheckBox::indicator:checked:disabled {
    border: 1px solid;
}

QCalendarWidget QWidget#qt_calendar_navigationbar {
    min-height: 32px;
}
QCalendarWidget QToolButton {
    min-width: 34px;
    padding: 0 6px;
    font-weight: 600;
}
QCalendarWidget QToolButton#qt_calendar_monthbutton {
    min-width: 120px;
    qproperty-autoRaise: true;
}
QCalendarWidget QToolButton#qt_calendar_yearbutton {
    min-width: 56px;
    qproperty-autoRaise: true;
}
QCalendarWidget QToolButton::menu-indicator {
    image: none;
    width: 0px;
}
""".strip()

LIGHT_COLORS_QSS = """
QWidget {
    color: #1f2937;
    background: #f3f6fb;
}
QMainWindow { background: #f3f6fb; }
QDialog { background: #f3f6fb; }

QLabel { color: #1f2937; }

QTabWidget::pane {
    border: 1px solid #c7d4ea;
    background: #ffffff;
}
QTabBar::tab {
    background: #e8eef9;
    color: #334155;
    border-color: #c7d4ea;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #0f172a;
    border-color: #7aa2e3;
}

QPushButton {
    background: #eef2fa;
    color: #1f2937;
    border-color: #bccae3;
}
QToolButton[toolbarAction="true"] {
    background: #eef2fa;
    border-color: #bccae3;
}
QToolButton[toolbarAction="true"]:hover {
    background: #dbeafe;
    border-color: #93c5fd;
}
QToolButton[infoIconAction="true"] {
    background: transparent;
}
QToolButton[infoIconAction="true"]:hover {
    background: rgba(30, 136, 229, 0.08);
}

QLineEdit, QTextEdit, QComboBox, QDateEdit, QListWidget {
    background: #ffffff;
    color: #111827;
    border-color: #bccae3;
}
QComboBox::drop-down, QDateEdit::drop-down {
    border-left-color: #bccae3;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QListWidget:focus {
    border-color: #2f6fe4;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #111827;
    border-color: #bccae3;
    selection-background-color: #dbeafe;
    selection-color: #0f172a;
}

QTableWidget {
    background: #ffffff;
    color: #111827;
    gridline-color: #d7e0ef;
    alternate-background-color: #f8fbff;
    border-color: #c7d4ea;
}
QHeaderView::section {
    background: #dde7f8;
    color: #1e293b;
    border-bottom-color: #c7d4ea;
}

QGroupBox {
    color: #1e293b;
    border-color: #c7d4ea;
}

QCheckBox::indicator {
    background: #ffffff;
    border-color: #374151;
}
QCheckBox::indicator:unchecked:hover {
    border-color: #1d4ed8;
}
QCheckBox::indicator:checked {
    background: #1d4ed8;
    border-color: #1d4ed8;
}
QCheckBox::indicator:disabled {
    background: #e5e7eb;
    border-color: #9ca3af;
}
QCheckBox::indicator:checked:disabled {
    background: #6b7280;
    border-color: #6b7280;
}

QLabel#errorText { color: #b42318; }

QCalendarWidget QToolButton {
    color: #0f172a;
}
""".strip()

DARK_COLORS_QSS = """
QWidget {
    color: #e5e7eb;
    background: #111827;
}
QMainWindow { background: #111827; }
QDialog { background: #111827; }

QLabel { color: #e5e7eb; }

QTabWidget::pane {
    border: 1px solid #374151;
    background: #1f2937;
}
QTabBar::tab {
    background: #1f2937;
    color: #cbd5e1;
    border-color: #374151;
}
QTabBar::tab:selected {
    background: #111827;
    color: #f9fafb;
    border-color: #60a5fa;
}

QPushButton {
    background: #1f2937;
    color: #f9fafb;
    border-color: #374151;
}
QToolButton[toolbarAction="true"] {
    background: #1f2937;
    border-color: #374151;
}
QToolButton[toolbarAction="true"]:hover {
    background: #243246;
    border-color: #60a5fa;
}
QToolButton[infoIconAction="true"] {
    background: transparent;
}
QToolButton[infoIconAction="true"]:hover {
    background: rgba(96, 165, 250, 0.16);
}

QLineEdit, QTextEdit, QComboBox, QDateEdit, QListWidget {
    background: #1f2937;
    color: #f9fafb;
    border-color: #374151;
}
QComboBox::drop-down, QDateEdit::drop-down {
    border-left-color: #374151;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QListWidget:focus {
    border-color: #60a5fa;
}
QComboBox QAbstractItemView {
    background: #1f2937;
    color: #f9fafb;
    border-color: #374151;
    selection-background-color: #1e3a8a;
    selection-color: #f9fafb;
}

QTableWidget {
    background: #1f2937;
    color: #f9fafb;
    gridline-color: #374151;
    alternate-background-color: #172131;
    border-color: #374151;
}
QHeaderView::section {
    background: #2b3b52;
    color: #f3f4f6;
    border-bottom-color: #374151;
}

QGroupBox {
    color: #e5e7eb;
    border-color: #374151;
}

QCheckBox::indicator {
    background: #1f2937;
    border-color: #9ca3af;
}
QCheckBox::indicator:unchecked:hover {
    border-color: #60a5fa;
}
QCheckBox::indicator:checked {
    background: #3b82f6;
    border-color: #3b82f6;
}
QCheckBox::indicator:disabled {
    background: #111827;
    border-color: #4b5563;
}
QCheckBox::indicator:checked:disabled {
    background: #4b5563;
    border-color: #4b5563;
}

QLabel#errorText { color: #fca5a5; }

QCalendarWidget QToolButton {
    color: #f9fafb;
}
""".strip()
