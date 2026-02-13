import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow, VISIBLE_COLUMNS
from csv_store import CsvStore

QApplication = qtwidgets.QApplication


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_column_widths_are_persisted_for_consultation_tabs(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    projeto_col = VISIBLE_COLUMNS.index("Projeto")

    win = MainWindow(store)
    win.t1_table.setColumnWidth(projeto_col, 210)
    win.t3_table.setColumnWidth(projeto_col, 260)
    win.t4_table.setColumnWidth(projeto_col, 310)
    win._save_preferences()
    win.close()

    reloaded = MainWindow(store)
    assert reloaded.t1_table.columnWidth(projeto_col) == 210
    assert reloaded.t3_table.columnWidth(projeto_col) == 260
    assert reloaded.t4_table.columnWidth(projeto_col) == 310
    reloaded.close()
