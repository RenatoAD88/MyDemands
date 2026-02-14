from datetime import date

import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtgui = pytest.importorskip("PySide6.QtGui", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

import app as app_module
from app import DeleteDemandDialog, MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog
Qt = qtcore.Qt
QKeyEvent = qtgui.QKeyEvent


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_delete_dialog_prefills_selected_data_on_pending_tabs(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    store.add(
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
    win.tabs.setCurrentIndex(1)
    win.refresh_tab3()
    win.t3_table.setCurrentCell(0, 0)

    capture = {"line_input": None, "loaded_rows": None}

    class FakeDeleteDialog:
        def __init__(self, parent, used_store):
            assert used_store is store
            capture["line_input"] = ""
            capture["loaded_rows"] = []

        def preload_selected_rows(self, rows):
            capture["line_input"] = ", ".join(str(r.get("ID", "")) for r in rows)
            capture["loaded_rows"] = rows

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(app_module, "DeleteDemandDialog", FakeDeleteDialog)

    win.delete_demand()

    assert capture["line_input"] == "1"
    assert len(capture["loaded_rows"]) == 1
    assert capture["loaded_rows"][0]["ID"] == "1"

    win.close()


def test_delete_on_concluded_tab_opens_delete_modal_with_prefill(tmp_path, monkeypatch):
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

    capture = {"line_input": None, "loaded_rows": None}

    class FakeDeleteDialog:
        def __init__(self, parent, used_store):
            assert used_store is store
            capture["line_input"] = ""
            capture["loaded_rows"] = []

        def preload_selected_rows(self, rows):
            capture["line_input"] = ", ".join(str(r.get("ID", "")) for r in rows)
            capture["loaded_rows"] = rows

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(app_module, "DeleteDemandDialog", FakeDeleteDialog)

    win.delete_demand()

    assert capture["line_input"] == "1"
    assert len(capture["loaded_rows"]) == 1
    assert capture["loaded_rows"][0]["Status"] == "Concluído"

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


def test_delete_dialog_enter_confirms_after_loading_rows(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    _id = store.add(
        {
            "Projeto": "Projeto Enter",
            "Descrição": "Exclusão via Enter",
            "Prioridade": "Baixa",
            "Prazo": today,
            "Data de Registro": today,
            "Status": "Concluído",
            "Data Conclusão": today,
            "Responsável": "Dani",
            "% Conclusão": "1",
        }
    )

    dlg = DeleteDemandDialog(None, store)
    dlg.line_input.setText("1")
    dlg._load_line()

    assert dlg.delete_btn.isEnabled()

    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    dlg.keyPressEvent(event)

    assert dlg.result() == QDialog.Accepted
    store.load()
    assert store.get(_id) is None


def test_delete_dialog_escape_cancels_and_resets_loaded_rows(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    store.add(
        {
            "Projeto": "Projeto Esc",
            "Descrição": "Cancelar via Esc",
            "Prioridade": "Baixa",
            "Prazo": today,
            "Data de Registro": today,
            "Status": "Em andamento",
            "Responsável": "Eva",
        }
    )

    dlg = DeleteDemandDialog(None, store)
    dlg.show()
    dlg.line_input.setText("1")
    dlg._load_line()

    assert dlg._loaded_rows

    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
    dlg.keyPressEvent(event)

    assert dlg.result() == QDialog.Rejected
    assert dlg._loaded_rows == []
    assert dlg.line_input.text() == ""

def test_delete_without_selection_opens_empty_modal(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))

    win = MainWindow(store)
    win.tabs.setCurrentIndex(1)
    win.refresh_tab3()

    capture = {"instantiated": False, "preloaded": False}

    class FakeDeleteDialog:
        def __init__(self, parent, used_store):
            assert used_store is store
            capture["instantiated"] = True

        def preload_selected_rows(self, rows):
            capture["preloaded"] = True

        def exec(self):
            return QDialog.Rejected

    monkeypatch.setattr(app_module, "DeleteDemandDialog", FakeDeleteDialog)

    win.delete_demand()

    assert capture["instantiated"] is True
    assert capture["preloaded"] is False

    win.close()
