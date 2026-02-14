from datetime import date, timedelta

import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_tab4_totals_label_shows_global_and_filtered_counts(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today()
    in_range = today.strftime("%d/%m/%Y")
    out_range = (today - timedelta(days=30)).strftime("%d/%m/%Y")

    store.add(
        {
            "Projeto": "P1",
            "Descrição": "Concluída no período",
            "Prioridade": "Alta",
            "Prazo": in_range,
            "Data de Registro": in_range,
            "Status": "Concluído",
            "Data Conclusão": in_range,
            "Responsável": "Ana",
            "% Conclusão": "100",
        }
    )
    store.add(
        {
            "Projeto": "P2",
            "Descrição": "Concluída fora do período",
            "Prioridade": "Média",
            "Prazo": out_range,
            "Data de Registro": out_range,
            "Status": "Concluído",
            "Data Conclusão": out_range,
            "Responsável": "Bia",
            "% Conclusão": "100",
        }
    )
    store.add(
        {
            "Projeto": "P3",
            "Descrição": "Pendente",
            "Prioridade": "Baixa",
            "Prazo": in_range,
            "Data de Registro": in_range,
            "Status": "Em andamento",
            "Responsável": "Caio",
        }
    )

    win = MainWindow(store)

    assert win.t4_totals_label.text() == "Total de demandas concluídas: 2 - Exibindo todas as demandas concluídas"
    assert win.t4_table.rowCount() == 2

    win.t4_start.setDate(win.t4_end.date())
    win.refresh_tab4()

    assert win.t4_totals_label.text() == "Total de demandas concluídas: 2 - Total de demandas filtradas: 1"
    assert win.t4_table.rowCount() == 1

    win._clear_tab4_filters()
    assert win.t4_totals_label.text() == "Total de demandas concluídas: 2 - Exibindo todas as demandas concluídas"
    assert win.t4_table.rowCount() == 2

    win.close()
