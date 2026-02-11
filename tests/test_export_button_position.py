import pytest


qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QToolButton = qtwidgets.QToolButton


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_export_button_is_not_between_new_and_delete(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    corner = win.tabs.cornerWidget()
    assert isinstance(corner, QToolButton)
    assert corner.objectName() == "exportAction"

    for i in range(win.t1_actions_layout.count()):
        item = win.t1_actions_layout.itemAt(i)
        widget = item.widget()
        if isinstance(widget, QToolButton):
            assert widget.objectName() != "exportAction"

    win.close()
