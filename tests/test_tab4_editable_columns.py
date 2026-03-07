import pytest

pytest.importorskip("PySide6", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow, TAB4_EDITABLE_COLUMNS, VISIBLE_COLUMNS
from csv_store import CsvStore

from PySide6.QtWidgets import QApplication


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_tab4_allows_status_editing():
    assert "Status" in TAB4_EDITABLE_COLUMNS


def test_tab4_data_registro_inline_edit_persists(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = store.add(
        {
            "Projeto": "Projeto A",
            "Descrição": "Demanda concluída",
            "Prioridade": "Alta",
            "Prazo": "12/02/2026",
            "Data de Registro": "01/02/2026",
            "Status": "Concluído",
            "Data Conclusão": "12/02/2026",
            "Responsável": "Ana",
            "% Conclusão": "1",
        }
    )

    win = MainWindow(store)
    win.tabs.setCurrentIndex(2)
    win.refresh_tab4()

    registro_col = VISIBLE_COLUMNS.index("Data de Registro")
    registro_item = win.t4_table.item(0, registro_col)
    assert registro_item is not None

    registro_item.setText("03/02/2026")

    store.load()
    updated = store.get(row_id)
    assert updated is not None
    assert updated.data["Data de Registro"] == "03/02/2026"

    win.close()
