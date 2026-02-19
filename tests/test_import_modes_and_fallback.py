import csv

import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore, DISPLAY_COLUMNS

QApplication = qtwidgets.QApplication
QFileDialog = qtwidgets.QFileDialog
QMessageBox = qtwidgets.QMessageBox


def _app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _row(id_value: str, projeto: str):
    row = {k: "" for k in DISPLAY_COLUMNS}
    row["ID"] = id_value
    row["É Urgente?"] = "Não"
    row["Status"] = "Não iniciada"
    row["Prioridade"] = "Média"
    row["Data de Registro"] = "01/01/2025"
    row["Prazo"] = "02/01/2025"
    row["Projeto"] = projeto
    row["Descrição"] = projeto
    row["% Conclusão"] = "0%"
    return row


def test_import_merge_behavior_rewrites_ids_and_appends_data(tmp_path):
    store = CsvStore(str(tmp_path))
    base = store.parse_exported_csv_text("\n".join([
        ",".join(DISPLAY_COLUMNS),
        ",".join([_row("1", "Local").get(c, "") for c in DISPLAY_COLUMNS]),
    ]))
    store.replace_with_rows(base)

    incoming_text = "\n".join([
        ",".join(DISPLAY_COLUMNS),
        ",".join([_row("1", "Importado 1").get(c, "") for c in DISPLAY_COLUMNS]),
        ",".join([_row("2", "Importado 2").get(c, "") for c in DISPLAY_COLUMNS]),
    ])
    imported = store.parse_exported_csv_text(incoming_text)
    store.merge_with_rows(imported)

    rows = store.build_view()
    assert len(rows) == 3
    assert [r["ID"] for r in rows] == ["1", "2", "3"]
    assert [r["Projeto"] for r in rows] == ["Local", "Importado 1", "Importado 2"]


def test_import_replace_clears_existing(tmp_path):
    store = CsvStore(str(tmp_path))
    store.add({"Projeto": "Antigo", "Descrição": "A", "Status": "Não iniciada", "Data de Registro": "01/01/2025", "Prazo": "02/01/2025"})

    incoming_text = "\n".join([
        ",".join(DISPLAY_COLUMNS),
        ",".join([_row("9", "Novo Só").get(c, "") for c in DISPLAY_COLUMNS]),
    ])
    imported = store.parse_exported_csv_text(incoming_text)
    store.replace_with_rows(imported)

    rows = store.build_view()
    assert len(rows) == 1
    assert rows[0]["Projeto"] == "Novo Só"


def test_incompatible_csv_offers_save_plain_copy(tmp_path, monkeypatch):
    _app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    source = tmp_path / "bad.csv"
    source.write_text("incompativel", encoding="utf-8")
    target = tmp_path / "copy.csv"

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(target), "CSV (*.csv)"))

    assert win._offer_save_plain_copy(str(source)) is True
    assert target.read_text(encoding="utf-8") == "incompativel"


def test_incompatible_decrypted_csv_offers_save_decrypted_copy(tmp_path, monkeypatch):
    _app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    source = tmp_path / "orig.csv"
    source.write_text("placeholder", encoding="utf-8")
    target = tmp_path / "decrypted.csv"

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(target), "CSV (*.csv)"))

    assert win._offer_save_decrypted_copy("ID,Projeto\n1,Teste\n", str(source)) is True
    assert target.read_text(encoding="utf-8-sig") == "ID,Projeto\n1,Teste\n"
