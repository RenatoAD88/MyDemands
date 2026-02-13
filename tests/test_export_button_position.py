import pytest


qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QToolButton = qtwidgets.QToolButton
QLabel = qtwidgets.QLabel


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_shortcuts_section_renders_buttons_above_tabs(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    export_button = win.findChild(QToolButton, "exportAction")
    assert export_button is not None

    primary_button = win.findChild(QToolButton, "primaryAction")
    danger_button = win.findChild(QToolButton, "dangerAction")
    assert primary_button is not None
    assert danger_button is not None

    import_button = win.findChild(QToolButton, "importAction")
    assert import_button is not None

    info_button = win.findChild(QToolButton, "infoAction")
    assert info_button is not None

    for btn in (primary_button, danger_button, export_button, import_button):
        assert bool(btn.property("toolbarAction")) is True

    assert bool(info_button.property("infoIconAction")) is True

    for i in range(win.t1_actions_layout.count()):
        item = win.t1_actions_layout.itemAt(i)
        widget = item.widget()
        if isinstance(widget, QToolButton):
            assert widget.objectName() not in {"primaryAction", "dangerAction", "exportAction", "importAction", "infoAction"}

    win.close()
