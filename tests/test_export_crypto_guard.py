import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QFileDialog = qtwidgets.QFileDialog
QInputDialog = qtwidgets.QInputDialog
QMessageBox = qtwidgets.QMessageBox


def _app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_export_does_not_prompt_passphrase_when_crypto_missing(tmp_path, monkeypatch):
    _app()
    store = CsvStore(str(tmp_path))
    store.add({
        "Descrição": "Demanda 1",
        "Projeto": "Projeto 1",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "Ana",
    })
    win = MainWindow(store)

    export_path = tmp_path / "secure_export.csv"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(export_path), "CSV (*.csv)"))
    monkeypatch.setattr(win.secure_csv_service, "crypto_ready", lambda: False)

    called = {"warning": 0, "prompt": 0}

    def _warning(*args, **kwargs):
        called["warning"] += 1
        return QMessageBox.Ok

    def _prompt(*args, **kwargs):
        called["prompt"] += 1
        raise AssertionError("QInputDialog.getText não deveria ser chamado quando crypto está indisponível")

    monkeypatch.setattr(QMessageBox, "warning", _warning)
    monkeypatch.setattr(QInputDialog, "getText", _prompt)

    win.export_demands_csv()

    assert called["warning"] == 1
    assert called["prompt"] == 0
    assert not export_path.exists()
