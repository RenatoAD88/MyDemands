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


def test_inline_edicao_data_nao_reverte_no_t3(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store)
    win = MainWindow(store)
    win.refresh_tab3()

    infos = []
    monkeypatch.setattr("app.QMessageBox.information", lambda *_args: infos.append(True))

    item = _cell(win, 0, "Prazo")
    item.setText("31/01/2026")

    assert store.get(row_id).data["Prazo"] == "31/01/2026"
    assert infos == []
    win.close()


def test_modal_salva_sem_bloqueio_por_validacao_global(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store)
    win = MainWindow(store)

    warnings = []
    monkeypatch.setattr("app.QMessageBox.warning", lambda *_args: warnings.append(True))

    source = store.get(row_id)

    class _FakeDialog:
        def __init__(self, *_args, **_kwargs):
            pass

        def setWindowTitle(self, *_args, **_kwargs):
            return None

        def exec(self):
            return qtwidgets.QDialog.Accepted

        def payload(self):
            data = dict(source.data)
            data["Prazo"] = "31/01/2026"
            return data

    monkeypatch.setattr("app.NewDemandDialog", _FakeDialog)
    win._open_demand_from_eisenhower_card(dict(source.data) | {"_id": row_id})

    assert warnings == []
    assert store.get(row_id).data["Prazo"] == "31/01/2026"
    win.close()
