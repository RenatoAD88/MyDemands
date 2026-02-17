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


def test_early_table_resize_callback_does_not_crash_without_tabs(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    table = win.t3_table
    delattr(win, "tabs")
    win._ui_ready = True

    # Simula disparo de sectionResized em estado inconsistente de inicialização.
    win._on_table_section_resized(table)

    win.close()
