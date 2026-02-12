from datetime import date

import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

import app as app_module
from app import DeleteDemandDialog, MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_delete_dialog_opens_without_prefilled_data_on_pending_tabs(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    _id = store.add(
        {
            "Projeto": "Projeto X",
            "Descrição": "Demanda pendente",
            "Prioridade": "Alta",
            "Prazo": date.today().strftime("%d/%m/%Y"),
            "Data de Registro": date.today().strftime("%d/%m/%Y"),
            "Status": "Em andamento",
            "Responsável": "Ana",
        }
    )

    win = MainWindow(store)
    win.tabs.setCurrentIndex(0)
    win.refresh_tab1()
    win.t1_table.setCurrentCell(0, 0)

    capture = {"line_input": None, "loaded_rows": None}

    class FakeDeleteDialog:
        def __init__(self, parent, used_store):
            assert used_store is store
            capture["line_input"] = ""
            capture["loaded_rows"] = []

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(app_module, "DeleteDemandDialog", FakeDeleteDialog)

    win.delete_demand()

    assert capture["line_input"] == ""
    assert capture["loaded_rows"] == []

    win.close()


def test_delete_on_concluded_tab_is_blocked_with_same_message(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    store.add(
        {
            "Projeto": "Projeto Y",
            "Descrição": "Demanda concluída",
            "Prioridade": "Média",
            "Prazo": today,
            "Data de Registro": today,
            "Status": "Concluído",
            "Data Conclusão": today,
            "Responsável": "Bia",
            "% Conclusão": "1",
        }
    )

    win = MainWindow(store)
    win.tabs.setCurrentIndex(2)
    win.refresh_tab4()
    win.t4_table.setCurrentCell(0, 0)

    warnings = []

    def fake_warning(parent, title, text):
        warnings.append((title, text))
        return 0

    monkeypatch.setattr(app_module.QMessageBox, "warning", fake_warning)

    class ShouldNotOpenDeleteDialog:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("DeleteDemandDialog não deve abrir na tab de concluídas")

    monkeypatch.setattr(app_module, "DeleteDemandDialog", ShouldNotOpenDeleteDialog)

    win.delete_demand()

    assert warnings == [("Bloqueado", "Demandas concluídas não podem ser excluídas.")]

    win.close()


def test_delete_dialog_cancel_discards_loaded_data_and_closes_modal(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    store.add(
        {
            "Projeto": "Projeto Z",
            "Descrição": "Demanda para cancelar exclusão",
            "Prioridade": "Baixa",
            "Prazo": today,
            "Data de Registro": today,
            "Status": "Em andamento",
            "Responsável": "Caio",
        }
    )

    dlg = DeleteDemandDialog(None, store)
    dlg.show()
    dlg.line_input.setText("1")
    dlg._load_line()

    assert dlg._loaded_rows
    assert dlg.delete_btn.isEnabled()

    dlg._cancel_delete_action()

    assert dlg.result() == QDialog.Rejected
    assert dlg._loaded_rows == []
    assert dlg.info_label.text() == ""
    assert dlg.line_input.text() == ""
    assert not dlg.delete_btn.isEnabled()
    assert not dlg.isVisible()
