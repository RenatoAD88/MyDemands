import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QMessageBox = qtwidgets.QMessageBox


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class _DummyCloseEvent:
    def __init__(self):
        self.ignored = False

    def ignore(self):
        self.ignored = True


def test_close_confirmation_uses_sim_nao_and_enter_escape_behavior(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    seen = {"checked": False}

    def fake_exec(dialog):
        yes_button = dialog.button(QMessageBox.Yes)
        no_button = dialog.button(QMessageBox.No)

        assert yes_button is not None
        assert no_button is not None
        assert yes_button.text() == "Sim"
        assert no_button.text() == "Não"
        assert dialog.defaultButton() is yes_button
        assert dialog.escapeButton() is no_button

        seen["checked"] = True
        return QMessageBox.No

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)

    close_event = _DummyCloseEvent()
    win.closeEvent(close_event)

    assert seen["checked"] is True
    assert close_event.ignored is True
    win.close()
