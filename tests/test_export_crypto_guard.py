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


def _build_window(tmp_path):
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
    return MainWindow(store)


def test_export_blocks_when_crypto_missing(tmp_path, monkeypatch):
    win = _build_window(tmp_path)

    export_path = tmp_path / "secure_export.csv"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(export_path), "CSV (*.csv)"))
    monkeypatch.setattr(win.secure_csv_service, "crypto_available", lambda: False)

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


def test_export_allows_when_crypto_available(tmp_path, monkeypatch):
    win = _build_window(tmp_path)

    export_path = tmp_path / "secure_export.csv"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(export_path), "CSV (*.csv)"))
    monkeypatch.setattr(win.secure_csv_service, "crypto_available", lambda: True)
    monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("senha-segura", True))

    monkeypatch.setattr(win.secure_csv_service, "render_csv_text", lambda rows: "ID,Projeto\n1,Projeto 1\n")
    monkeypatch.setattr(win.secure_csv_service, "export_payload", lambda csv_text, passphrase, is_master: "MYDEMANDS_ENCRYPTED_V1\ndata:abc")

    infos = {"count": 0}
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: infos.__setitem__("count", infos["count"] + 1))

    win.export_demands_csv()

    assert export_path.exists()
    assert export_path.read_text(encoding="utf-8").startswith("MYDEMANDS_ENCRYPTED_V1")
    assert infos["count"] == 1
