from datetime import date

import pytest

qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow, VISIBLE_COLUMNS
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
Qt = qtcore.Qt


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _build_store_with_priorities(tmp_path):
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    for prioridade in ["Baixa", "Alta", "Média"]:
        store.add(
            {
                "Projeto": f"Projeto {prioridade}",
                "Descrição": f"Demanda {prioridade}",
                "Prioridade": prioridade,
                "Prazo": today,
                "Data de Registro": today,
                "Status": "Em andamento",
                "Responsável": "Ana",
                "% Conclusão": "0.5",
            }
        )
    return store


def _priorities_from_table(table):
    col = VISIBLE_COLUMNS.index("Prioridade")
    return [table.item(row, col).text() for row in range(table.rowCount())]


def test_t3_and_t4_first_column_header_uses_numero_label(tmp_path):
    _get_app()
    store = _build_store_with_priorities(tmp_path)

    win = MainWindow(store)

    assert win.t3_table.horizontalHeaderItem(0).text() == "Nº"
    assert win.t4_table.horizontalHeaderItem(0).text() == "Nº"

    win.close()


def test_t3_priority_sort_uses_criticidade_order(tmp_path):
    _get_app()
    store = _build_store_with_priorities(tmp_path)

    win = MainWindow(store)
    col = VISIBLE_COLUMNS.index("Prioridade")

    win._on_header_sort_requested(win.t3_table, col, Qt.AscendingOrder)
    assert _priorities_from_table(win.t3_table) == ["Alta", "Média", "Baixa"]

    win._on_header_sort_requested(win.t3_table, col, Qt.DescendingOrder)
    assert _priorities_from_table(win.t3_table) == ["Baixa", "Média", "Alta"]

    win.close()


def test_t4_priority_sort_uses_criticidade_order(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    for prioridade in ["Baixa", "Alta", "Média"]:
        store.add(
            {
                "Projeto": f"Projeto {prioridade}",
                "Descrição": f"Demanda concluída {prioridade}",
                "Prioridade": prioridade,
                "Prazo": today,
                "Data de Registro": today,
                "Status": "Concluído",
                "Data Conclusão": today,
                "Responsável": "Ana",
                "% Conclusão": "1",
            }
        )

    win = MainWindow(store)
    col = VISIBLE_COLUMNS.index("Prioridade")

    win._on_header_sort_requested(win.t4_table, col, Qt.AscendingOrder)
    assert _priorities_from_table(win.t4_table) == ["Alta", "Média", "Baixa"]

    win._on_header_sort_requested(win.t4_table, col, Qt.DescendingOrder)
    assert _priorities_from_table(win.t4_table) == ["Baixa", "Média", "Alta"]

    win.close()
