import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtgui = pytest.importorskip("PySide6.QtGui", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import DemandTable

QApplication = qtwidgets.QApplication
Qt = qtcore.Qt
QKeyEvent = qtgui.QKeyEvent


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_delete_key_calls_handler_even_without_selected_rows():
    _get_app()
    table = DemandTable(0, 1)

    calls = {"count": 0}

    def handler(_table):
        calls["count"] += 1
        return True

    table.set_delete_demand_handler(handler)

    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
    table.keyPressEvent(event)

    assert calls["count"] == 1
