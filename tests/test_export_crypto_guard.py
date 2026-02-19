import csv

import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore, EXPORT_VERSION_PREFIX, EXPORT_TEMPLATE_VERSION

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


def test_export_writes_plain_csv_with_template_version(tmp_path, monkeypatch):
    win = _build_window(tmp_path)

    export_path = tmp_path / "export.csv"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(export_path), "CSV (*.csv)"))

    infos = {"count": 0, "text": ""}

    def _info(_self, _title, text):
        infos["count"] += 1
        infos["text"] = text

    monkeypatch.setattr(QMessageBox, "information", _info)

    win.export_demands_csv()

    assert export_path.exists()
    raw = export_path.read_text(encoding="utf-8-sig")
    assert raw.startswith(f"{EXPORT_VERSION_PREFIX}{EXPORT_TEMPLATE_VERSION}\n")

    lines = raw.splitlines()
    rows = list(csv.DictReader(lines[1:]))
    assert len(rows) == 1
    assert rows[0]["Projeto"] == "Projeto 1"
    assert infos["count"] == 1
    assert "Total de demandas: 1" in infos["text"]
