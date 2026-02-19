import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore
from mydemands.services.theme_service import ThemeService

QApplication = qtwidgets.QApplication
QLineEdit = qtwidgets.QLineEdit
QPushButton = qtwidgets.QPushButton
QTabBar = qtwidgets.QTabBar
QToolButton = qtwidgets.QToolButton
QTableWidget = qtwidgets.QTableWidget


def _app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _metrics(win: MainWindow) -> dict[str, int]:
    app = QApplication.instance()
    assert app is not None
    app.processEvents()

    tab_bar = win.findChild(QTabBar)
    assert tab_bar is not None
    tab_h = tab_bar.tabRect(0).height() if tab_bar.count() else tab_bar.sizeHint().height()

    toolbar_btn = next(btn for btn in win.findChildren(QToolButton) if bool(btn.property("toolbarAction")))
    line_edit = win.findChild(QLineEdit)
    push_btn = win.findChild(QPushButton)

    assert line_edit is not None
    assert push_btn is not None

    table = win.findChild(QTableWidget)
    assert table is not None
    header = table.horizontalHeader()

    return {
        "toolbar_button_hint": toolbar_btn.sizeHint().height(),
        "toolbar_button_icon": toolbar_btn.iconSize().height(),
        "lineedit_min": line_edit.minimumHeight(),
        "lineedit_hint": line_edit.sizeHint().height(),
        "button_hint": push_btn.sizeHint().height(),
        "tab_height": tab_h,
        "header_height": header.height(),
    }


def test_dark_theme_keeps_same_mainwindow_metrics(tmp_path):
    app = _app()
    theme = ThemeService(app)
    win = MainWindow(CsvStore(str(tmp_path)), theme_service=theme)
    win.show()

    theme.apply_theme("light")
    light = _metrics(win)

    theme.apply_theme("dark")
    dark = _metrics(win)

    assert dark == light
