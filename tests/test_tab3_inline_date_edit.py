import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow, VISIBLE_COLUMNS
from csv_store import CsvStore


QApplication = qtwidgets.QApplication


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _add_pending(store: CsvStore, **extra):
    payload = {
        "Descrição": "Demanda",
        "Projeto": "Projeto",
        "Prioridade": "Alta",
        "Prazo": "10/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "R",
        "% Conclusão": "0.25",
        "É Urgente?": "Não",
    }
    payload.update(extra)
    return store.add(payload)


def _cell(win: MainWindow, row: int, col_name: str):
    return win.t3_table.item(row, VISIBLE_COLUMNS.index(col_name))


def test_inline_prazo_edit_persists_without_modal(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store)
    win = MainWindow(store)
    win.refresh_tab3()

    monkeypatch.setattr("app.PrazoMultiDialog", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("modal não deve abrir")))

    item = _cell(win, 0, "Prazo")
    item.setText("11/02/2026")

    assert store.get(row_id).data["Prazo"] == "11/02/2026"
    win.close()


def test_inline_data_conclusao_updates_status_and_timing(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store)
    win = MainWindow(store)
    win.refresh_tab3()

    item = _cell(win, 0, "Data Conclusão")
    item.setText("09/02/2026")

    updated = store.get(row_id).data
    assert updated["Data Conclusão"] == "09/02/2026"
    assert updated["Status"] == "Concluído"
    assert updated["% Conclusão"] == "1"

    win.refresh_tab3()
    timing = _cell(win, 0, "Timing").text()
    assert timing in {"Concluído antes do prazo", "Concluído no prazo", "Concluída com atraso"}
    win.close()


def test_inline_edit_blocked_for_cancelled(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store, Status="Cancelado", **{"% Conclusão": "0", "Prazo": "10/02/2026"})
    win = MainWindow(store)
    win.refresh_tab3()

    infos = []
    monkeypatch.setattr("app.QMessageBox.information", lambda *_args: infos.append(True))

    item = _cell(win, 0, "Prazo")
    original = item.text()
    item.setText("12/02/2026")

    assert _cell(win, 0, "Prazo").text() == original
    assert infos
    win.close()


def test_inline_data_registro_edit_persists(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store)
    win = MainWindow(store)
    win.refresh_tab3()

    item = _cell(win, 0, "Data de Registro")
    item.setText("03/02/2026")

    updated = store.get(row_id).data
    assert updated["Data de Registro"] == "03/02/2026"
    win.close()


def test_inline_data_registro_uses_date_picker_editor(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store)
    win = MainWindow(store)
    win.refresh_tab3()

    model = win.t3_table.model()
    idx = model.index(0, VISIBLE_COLUMNS.index("Data de Registro"))
    delegate = win.t3_table.itemDelegate()
    editor = delegate.createEditor(win.t3_table, None, idx)

    assert editor is not None
    assert editor.metaObject().className() == "QDateEdit"
    assert editor.calendarPopup() is True
    win.close()
