import pytest


qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QToolButton = qtwidgets.QToolButton
QLabel = qtwidgets.QLabel
QPushButton = qtwidgets.QPushButton


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_shortcuts_section_renders_buttons_above_tabs(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    section_label = win.findChild(QLabel, "shortcutsSectionLabel")
    assert section_label is not None
    assert section_label.text() == "Atalhos"

    export_label = win.findChild(QLabel, "exportShortcutLabel")
    assert export_label is not None
    assert export_label.text() == "Exportar"

    export_button = win.findChild(QToolButton, "exportAction")
    assert export_button is not None

    primary_button = win.findChild(QPushButton, "primaryAction")
    danger_button = win.findChild(QPushButton, "dangerAction")
    assert primary_button is not None
    assert danger_button is not None

    for i in range(win.t1_actions_layout.count()):
        item = win.t1_actions_layout.itemAt(i)
        widget = item.widget()
        if isinstance(widget, QPushButton):
            assert widget.objectName() not in {"primaryAction", "dangerAction"}

    win.close()
