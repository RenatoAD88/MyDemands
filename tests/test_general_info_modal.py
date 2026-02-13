import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog
QPushButton = qtwidgets.QPushButton


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_general_info_modal_has_no_close_button(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    seen = {"checked": False}

    def fake_exec(dialog):
        if dialog.windowTitle() == "Informações gerais":
            buttons = [btn.text().strip() for btn in dialog.findChildren(QPushButton)]
            assert "Fechar" not in buttons
            seen["checked"] = True
        return 0

    monkeypatch.setattr(QDialog, "exec", fake_exec)

    win.show_general_information()

    assert seen["checked"] is True
    win.close()
