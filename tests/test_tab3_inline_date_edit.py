from pathlib import Path
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
    assert win.t3_table.rowCount() == 1
    assert _cell(win, 0, "Data de Registro").text() == "03/02/2026"
    win.close()


def test_inline_data_registro_invalida_reverte_sem_sumir_tabela(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store)
    win = MainWindow(store)
    win.refresh_tab3()

    infos = []
    monkeypatch.setattr("app.QMessageBox.information", lambda *_args: infos.append(True))

    item = _cell(win, 0, "Data de Registro")
    original = item.text()
    item.setText("31/31/2026")

    assert win.t3_table.rowCount() == 1
    assert _cell(win, 0, "Data de Registro").text() == original
    assert infos
    win.close()


def test_inline_urgencia_refresh_consistente_sem_refresh_magico(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store, **{"É Urgente?": "Não"})
    win = MainWindow(store)
    win.refresh_tab3()

    item = _cell(win, 0, "É Urgente?")
    item.setText("Sim")

    assert store.get(row_id).data["É Urgente?"] == "Sim"
    assert win.t3_table.rowCount() == 1
    assert _cell(win, 0, "É Urgente?").text() == "Sim"
    assert _cell(win, 0, "Descrição").text() == "Demanda"
    win.close()


def test_inline_reentrancia_ignora_item_changed_durante_revert(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store)
    win = MainWindow(store)
    win.refresh_tab3()

    calls = {"count": 0}
    real_handler = win._on_item_changed

    def _wrapped_handler(changed_item):
        calls["count"] += 1
        return real_handler(changed_item)

    win.t3_table.itemChanged.disconnect(win._on_item_changed)
    win._on_item_changed = _wrapped_handler
    win.t3_table.itemChanged.connect(win._on_item_changed)

    monkeypatch.setattr("app.QMessageBox.information", lambda *_args: None)
    item = _cell(win, 0, "Data de Registro")
    item.setText("99/99/9999")

    assert calls["count"] == 1
    assert win.t3_table.rowCount() == 1
    win.close()


def test_inline_data_registro_datepicker_abre_no_mes_ano_corrente(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store, **{"Data de Registro": "01/01/2024"})
    win = MainWindow(store)
    win.refresh_tab3()

    model = win.t3_table.model()
    idx = model.index(0, VISIBLE_COLUMNS.index("Data de Registro"))
    delegate = win.t3_table.itemDelegate()
    editor = delegate.createEditor(win.t3_table, None, idx)
    delegate.setEditorData(editor, idx)

    calendar = editor.calendarWidget()
    today = editor.date().currentDate()
    assert calendar.yearShown() == today.year()
    assert calendar.monthShown() == today.month()
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


def test_inline_status_edit_persists_and_updates_views(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store, Status="Em andamento")
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    item = _cell(win, 0, "Status")
    item.setText("Bloqueado")

    assert store.get(row_id).data["Status"] == "Bloqueado"
    grouped = win.t3_eisenhower_view.last_groups
    assert any(r.get("_id") == row_id for rows in grouped.values() for r in rows)
    win.close()


def test_inline_percent_edit_persists_and_normalizes(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store, **{"% Conclusão": "0.25"})
    win = MainWindow(store)
    win.refresh_tab3()

    item = _cell(win, 0, "% Conclusão")
    item.setText("50%")

    assert store.get(row_id).data["% Conclusão"] == "0.5"
    assert _cell(win, 0, "% Conclusão").text() == "50%"
    win.close()


def test_inline_long_text_fields_and_csv_persistence(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store)
    win = MainWindow(store)
    win.refresh_tab3()

    desc = "Descrição inline " * 12
    comm = "Comentário inline " * 12
    _cell(win, 0, "Descrição").setText(desc)
    _cell(win, 0, "Comentário").setText(comm)

    data = store.get(row_id).data
    assert data["Descrição"] == desc.strip()
    assert data["Comentário"] == comm.strip()

    csv_text = store.csv_path and Path(store.csv_path).read_text(encoding="utf-8-sig")
    assert desc.strip() in csv_text
    assert comm.strip() in csv_text
    win.close()


def test_inline_keeps_correct_row_under_filter_and_sort(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    first = _add_pending(store, Descrição="AAA", Responsável="R1", Projeto="P1")
    second = _add_pending(store, Descrição="BBB", Responsável="R2", Projeto="P2")
    win = MainWindow(store)
    win.refresh_tab3()

    win.t3_responsavel.setText("R2")
    win.refresh_tab3()
    assert win.t3_table.rowCount() == 1

    item = _cell(win, 0, "Data de Registro")
    item.setText("04/02/2026")

    assert store.get(second).data["Data de Registro"] == "04/02/2026"
    assert store.get(first).data["Data de Registro"] == "01/02/2026"
    win.close()


def test_inline_invalid_percent_shows_specific_error_and_reverts(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store, **{"% Conclusão": "0.25"})
    win = MainWindow(store)
    win.refresh_tab3()

    warnings = []
    monkeypatch.setattr("app.QMessageBox.warning", lambda *_args: warnings.append(_args[2] if len(_args) > 2 else ""))

    item = _cell(win, 0, "% Conclusão")
    old = item.text()
    item.setText("250%")

    assert _cell(win, 0, "% Conclusão").text() == old
    assert any("% Conclusão inválido" in w or "fora do intervalo" in w for w in warnings)
    assert win.t3_table.rowCount() == 1
    win.close()


def test_inline_prazo_edit_persists_to_csv_and_eisenhower(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store, Prazo="10/02/2026")
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    _cell(win, 0, "Prazo").setText("12/02/2026")

    assert store.get(row_id).data["Prazo"] == "12/02/2026"
    grouped = win.t3_eisenhower_view.last_groups
    assert any(r.get("_id") == row_id for rows in grouped.values() for r in rows)
    csv_text = Path(store.csv_path).read_text(encoding="utf-8-sig")
    assert "12/02/2026" in csv_text
    win.close()
