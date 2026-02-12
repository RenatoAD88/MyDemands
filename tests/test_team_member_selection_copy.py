import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import selected_member_names

QApplication = qtwidgets.QApplication
QTableWidget = qtwidgets.QTableWidget
QTableWidgetItem = qtwidgets.QTableWidgetItem


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_selected_member_names_ignores_footer_and_deduplicates_rows():
    _get_app()
    table = QTableWidget(3, 2)
    table.setItem(0, 0, QTableWidgetItem("Alice"))
    table.setItem(0, 1, QTableWidgetItem("K"))
    table.setItem(1, 0, QTableWidgetItem("Bob"))
    table.setItem(1, 1, QTableWidgetItem("P"))
    table.setItem(2, 0, QTableWidgetItem("Participação Dia"))
    table.setItem(2, 1, QTableWidgetItem("2"))

    table.item(0, 1).setSelected(True)
    table.item(0, 0).setSelected(True)
    table.item(1, 1).setSelected(True)
    table.item(2, 0).setSelected(True)

    assert selected_member_names(table) == ["Alice", "Bob"]
