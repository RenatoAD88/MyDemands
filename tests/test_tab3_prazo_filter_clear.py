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


def test_tab3_reset_clears_prazo_filter_to_all(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    win.t3_prazo.setDate(win.t3_prazo.minimumDate().addDays(5))
    assert win.t3_prazo.date() != win.t3_prazo.minimumDate()

    win._reset_tab3_filters()

    assert win.t3_prazo.date() == win.t3_prazo.minimumDate()
    win.close()
