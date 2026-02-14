from datetime import date

import pytest

qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

import app as app_module
from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog
Qt = qtcore.Qt


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_concluded_table_supports_duplicate_and_resets_conclusion_fields(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    store.add(
        {
            "Projeto": "Projeto Concluído",
            "Descrição": "Demanda finalizada para duplicar",
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
    win.t4_table.setCurrentCell(0, 0)

    assert win.t4_table.contextMenuPolicy() == Qt.CustomContextMenu

    captured = {"initial_data": None}

    class FakeNewDemandDialog:
        def __init__(self, parent, initial_data=None):
            captured["initial_data"] = dict(initial_data or {})

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(app_module, "NewDemandDialog", FakeNewDemandDialog)

    win._duplicate_selected_demand(win.t4_table)

    assert captured["initial_data"] is not None
    assert captured["initial_data"]["Projeto"] == "Projeto Concluído"
    assert captured["initial_data"]["Descrição"] == "Demanda finalizada para duplicar"
    assert captured["initial_data"]["Status"] == ""
    assert captured["initial_data"]["% Conclusão"] == ""
    assert captured["initial_data"]["Data Conclusão"] == ""

    win.close()


def test_duplicate_concluded_demand_shows_pending_modal_with_created_id(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    store.add(
        {
            "Projeto": "Projeto Concluído",
            "Descrição": "Demanda finalizada para duplicar",
            "Prioridade": "Alta",
            "Prazo": today,
            "Data de Registro": today,
            "Status": "Concluído",
            "Data Conclusão": today,
            "Responsável": "Ana",
            "% Conclusão": "1",
        }
    )

    captured = {"demand_id": None}

    def fake_modal(self, demand_id):
        captured["demand_id"] = demand_id

    class FakeNewDemandDialog:
        def __init__(self, parent, initial_data=None):
            self._payload = dict(initial_data or {})

        def exec(self):
            return QDialog.Accepted

        def payload(self):
            return self._payload

    monkeypatch.setattr(app_module, "NewDemandDialog", FakeNewDemandDialog)
    monkeypatch.setattr(MainWindow, "_show_duplicate_success_modal", fake_modal)

    win = MainWindow(store)
    win.tabs.setCurrentIndex(2)
    win.refresh_tab4()
    win.t4_table.setCurrentCell(0, 0)

    win._duplicate_selected_demand(win.t4_table)

    assert captured["demand_id"].isdigit()

    win.close()


def test_duplicate_non_concluded_demand_does_not_show_pending_modal(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    store.add(
        {
            "Projeto": "Projeto Pendente",
            "Descrição": "Demanda em andamento para duplicar",
            "Prioridade": "Alta",
            "Prazo": today,
            "Data de Registro": today,
            "Status": "Pendente",
            "Data Conclusão": "",
            "Responsável": "Ana",
            "% Conclusão": "0.5",
        }
    )

    captured = {"called": False}

    def fake_modal(self, demand_id):
        captured["called"] = True

    class FakeNewDemandDialog:
        def __init__(self, parent, initial_data=None):
            self._payload = dict(initial_data or {})

        def exec(self):
            return QDialog.Accepted

        def payload(self):
            return self._payload

    monkeypatch.setattr(app_module, "NewDemandDialog", FakeNewDemandDialog)
    monkeypatch.setattr(MainWindow, "_show_duplicate_success_modal", fake_modal)

    win = MainWindow(store)
    win.tabs.setCurrentIndex(0)
    win.refresh_tab1()
    win.t1_table.setCurrentCell(0, 0)

    win._duplicate_selected_demand(win.t1_table)

    assert captured["called"] is False

    win.close()
