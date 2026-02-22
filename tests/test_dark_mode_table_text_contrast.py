import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtgui = pytest.importorskip("PySide6.QtGui", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow, VISIBLE_COLUMNS
from csv_store import CsvStore
from mydemands.services.theme_service import ThemeService

QApplication = qtwidgets.QApplication
QColor = qtgui.QColor
Qt = qtcore.Qt


def _app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _assert_column_foreground_not_black(win: MainWindow, table_key: str, column_name: str) -> None:
    table = win._make_table(table_key)
    row = table.rowCount()
    table.insertRow(row)
    col = VISIBLE_COLUMNS.index(column_name)
    win._set_item(table, row, col, "Valor teste", "1")
    item = table.item(row, col)
    assert item is not None
    brush = item.foreground()
    assert brush.style() != Qt.NoBrush
    assert brush.color() != QColor("black")


def test_dark_theme_status_timing_prazo_foreground_uses_dynamic_palette(tmp_path):
    app = _app()
    theme = ThemeService(app)
    store = CsvStore(str(tmp_path))
    win = MainWindow(store, theme_service=theme)

    theme.apply_theme("dark")

    for table_key in ("t3", "t4", "t4_cancelled"):
        for column_name in ("Status", "Timing", "Prazo"):
            _assert_column_foreground_not_black(win, table_key, column_name)


def test_dark_theme_prazo_values_follow_theme_palette(tmp_path):
    app = _app()
    theme = ThemeService(app)
    store = CsvStore(str(tmp_path))
    win = MainWindow(store, theme_service=theme)

    theme.apply_theme("dark")

    table = win._make_table("t3")
    col = VISIBLE_COLUMNS.index("Prazo")

    row_non_today = table.rowCount()
    table.insertRow(row_non_today)
    win._set_item(table, row_non_today, col, "01/01/2099", "1")
    non_today_item = table.item(row_non_today, col)
    assert non_today_item is not None
    assert non_today_item.foreground().color() == QColor(255, 255, 255)

    from datetime import date
    today_str = date.today().strftime("%d/%m/%Y")
    row_today = table.rowCount()
    table.insertRow(row_today)
    win._set_item(table, row_today, col, today_str, "2")
    today_item = table.item(row_today, col)
    assert today_item is not None
    assert today_item.foreground().color() == QColor(255, 255, 255)
