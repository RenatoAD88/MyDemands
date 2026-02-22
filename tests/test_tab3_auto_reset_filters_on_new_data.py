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


def _add_pending(store: CsvStore, suffix: str = "") -> None:
    store.add(
        {
            "Descrição": f"Demanda {suffix}".strip(),
            "Projeto": "Projeto X",
            "Prioridade": "Alta",
            "Prazo": "05/02/2026",
            "Data de Registro": "01/02/2026",
            "Status": "Em andamento",
            "Responsável": "Ana",
            "% Conclusão": "0.25",
        }
    )


def test_tab3_auto_resets_filters_once_when_pending_exists_and_no_result(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store, "A")

    win = MainWindow(store)

    # Simula filtro remanescente após limpar a massa.
    win.t3_search.setText("inexistente")
    win.refresh_tab3()

    # Ainda havia dados pendentes, então filtro inválido foi resetado automaticamente.
    assert win.t3_search.text() == ""
    assert win.t3_table.rowCount() >= 1

    win.close()
