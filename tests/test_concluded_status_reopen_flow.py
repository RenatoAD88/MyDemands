from datetime import date

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


def test_status_change_in_concluded_tab_reopens_demand(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    _id = store.add(
        {
            "Projeto": "Projeto A",
            "Descrição": "Demanda concluída",
            "Prioridade": "Alta",
            "Prazo": today,
            "Data de Registro": today,
            "Status": "Concluído",
            "Data Conclusão": today,
            "Responsável": "Ana",
            "% Conclusão": "1",
        }
    )

    win = MainWindow(store)
    win.tabs.setCurrentIndex(2)
    win.refresh_tab4()

    monkeypatch.setattr(win, "_prompt_percent_when_unconcluding", lambda: "0.5")

    status_col = VISIBLE_COLUMNS.index("Status")
    status_item = win.t4_table.item(0, status_col)
    assert status_item is not None

    status_item.setText("Em andamento")

    store.load()
    updated = store.get(_id)
    assert updated is not None
    assert updated.data["Status"] == "Em andamento"
    assert updated.data["Data Conclusão"] == ""
    assert updated.data["% Conclusão"] == "0.5"

    pending_rows = store.tab_pending_all()
    assert any(row["_id"] == _id for row in pending_rows)

    win.close()
