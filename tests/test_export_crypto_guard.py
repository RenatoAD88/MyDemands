import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QFileDialog = qtwidgets.QFileDialog
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

    called = {"warning": 0}

    def _warning(*args, **kwargs):
        called["warning"] += 1
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "warning", _warning)

    win.export_demands_csv()

    assert called["warning"] == 1
    assert not export_path.exists()


def test_export_generates_and_uses_passphrase(tmp_path, monkeypatch):
    win = _build_window(tmp_path)

    export_path = tmp_path / "secure_export.csv"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(export_path), "CSV (*.csv)"))
    monkeypatch.setattr(win.secure_csv_service, "crypto_available", lambda: True)
    monkeypatch.setattr(win.secure_csv_service, "generate_passphrase", lambda: "senha-gerada-123")

    monkeypatch.setattr(win.secure_csv_service, "render_csv_text", lambda rows: "ID,Projeto\n1,Projeto 1\n")

    captured = {}

    def _export(csv_text, passphrase, is_master):
        captured["passphrase"] = passphrase
        captured["is_master"] = is_master
        return "MYDEMANDS_ENCRYPTED_V1\ndata:abc"

    monkeypatch.setattr(win.secure_csv_service, "export_payload", _export)

    infos = {"count": 0, "text": ""}

    def _info(_self, _title, text):
        infos["count"] += 1
        infos["text"] = text

    monkeypatch.setattr(QMessageBox, "information", _info)

    win.export_demands_csv()

    assert export_path.exists()
    assert export_path.read_text(encoding="utf-8").startswith("MYDEMANDS_ENCRYPTED_V1")
    assert infos["count"] == 1
    assert "senha-gerada-123" in infos["text"]
    assert captured["passphrase"] == "senha-gerada-123"
    assert captured["is_master"] is False
