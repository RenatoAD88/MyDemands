from datetime import date

import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow, NewDemandDialog, PERCENT_LABEL_OPTIONS
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _build_valid_dialog_payload(dialog: NewDemandDialog):
    today = date.today().strftime("%d/%m/%Y")
    dialog.descricao.setPlainText("Implementar regra de conclusão")
    dialog.prioridade.setCurrentText("Alta")
    dialog.status.setCurrentText("Em andamento")
    dialog.responsavel.setText("Ana")
    dialog.projeto.setText("Projeto X")
    dialog.prazo_list.addItem(today)


def test_create_or_duplicate_blocks_100_percent_when_status_not_concluded():
    _get_app()
    dialog = NewDemandDialog(None)
    _build_valid_dialog_payload(dialog)
    dialog.perc.setCurrentText("100% - Concluído")

    dialog._on_save()

    assert dialog.result() != QDialog.Accepted
    assert "Não é possível criar uma demanda 100% concluída" in dialog.inline_error.text()


def test_concluded_tab_percent_prompt_uses_dropdown_with_same_options(monkeypatch, tmp_path):
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

    captured = {}

    def fake_get_item(parent, title, label, items, current, editable):
        captured["title"] = title
        captured["label"] = label
        captured["items"] = list(items)
        return ("50% - Parcial", True)

    monkeypatch.setattr(qtwidgets.QInputDialog, "getItem", fake_get_item)

    picked = win._prompt_percent_when_unconcluding()

    assert picked == "0.5"
    assert captured["title"] == "% Conclusão"
    assert captured["items"] == PERCENT_LABEL_OPTIONS

    # sanity: registro ainda existe
    assert store.get(_id) is not None
    win.close()
