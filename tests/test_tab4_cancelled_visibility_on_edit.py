from datetime import date

import pytest

pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow, VISIBLE_COLUMNS
from ui_theme import build_app_stylesheet
from csv_store import CsvStore

QApplication = qtwidgets.QApplication


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_cancelled_section_stays_visible_while_checkbox_is_checked_after_edit(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    today = date.today().strftime("%d/%m/%Y")
    _id = store.add(
        {
            "Projeto": "Projeto A",
            "Descrição": "Demanda cancelada",
            "Prioridade": "Alta",
            "Prazo": today,
            "Data de Registro": today,
            "Status": "Cancelado",
            "Data Conclusão": "",
            "Responsável": "Ana",
            "% Conclusão": "0",
        }
    )

    win = MainWindow(store)
    win.tabs.setCurrentIndex(2)
    win.t4_show_cancelled.setChecked(True)

    assert win.t4_cancelled_section.isVisible()
    assert win.t4_cancelled_table.rowCount() == 1

    responsavel_col = VISIBLE_COLUMNS.index("Responsável")
    responsavel_item = win.t4_cancelled_table.item(0, responsavel_col)
    assert responsavel_item is not None

    responsavel_item.setText("Beatriz")

    assert win.t4_show_cancelled.isChecked()
    assert win.t4_cancelled_section.isVisible()
    assert win.t4_cancelled_table.rowCount() == 1

    store.load()
    updated = store.get(_id)
    assert updated is not None
    assert updated.data["Responsável"] == "Beatriz"

    win.t4_show_cancelled.setChecked(False)
    assert not win.t4_cancelled_section.isVisible()

    win.close()


def test_checkboxes_use_white_background_with_visible_border_when_checked(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    stylesheet = build_app_stylesheet("light")
    assert "QCheckBox::indicator:checked" in stylesheet
    assert "background: #ffffff;" in stylesheet
    assert "border: 1px solid #111827;" in stylesheet

    win.close()
