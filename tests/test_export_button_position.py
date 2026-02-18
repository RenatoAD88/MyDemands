import pytest


qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore
from mydemands.services.theme_service import ThemeService

QApplication = qtwidgets.QApplication
QToolButton = qtwidgets.QToolButton
QLabel = qtwidgets.QLabel


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_shortcuts_section_renders_buttons_above_tabs(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    export_button = win.findChild(QToolButton, "exportAction")
    assert export_button is not None

    primary_button = win.findChild(QToolButton, "primaryAction")
    danger_button = win.findChild(QToolButton, "dangerAction")
    assert primary_button is not None
    assert danger_button is not None

    import_button = win.findChild(QToolButton, "importAction")
    assert import_button is not None

    info_button = win.findChild(QToolButton, "infoAction")
    assert info_button is not None

    for btn in (primary_button, danger_button, export_button, import_button):
        assert bool(btn.property("toolbarAction")) is True

    assert bool(info_button.property("infoIconAction")) is True

    for i in range(win.t1_actions_layout.count()):
        item = win.t1_actions_layout.itemAt(i)
        widget = item.widget()
        if isinstance(widget, QToolButton):
            assert widget.objectName() not in {"primaryAction", "dangerAction", "exportAction", "importAction", "infoAction"}

    win.close()


def test_shortcuts_icons_update_with_same_size_after_theme_switch(tmp_path):
    app = _get_app()
    store = CsvStore(str(tmp_path))
    theme = ThemeService(app)
    win = MainWindow(store, theme_service=theme)

    export_button = win.findChild(QToolButton, "exportAction")
    import_button = win.findChild(QToolButton, "importAction")

    assert export_button is not None
    assert import_button is not None

    light_export_size = export_button.iconSize()
    light_import_size = import_button.iconSize()

    theme.apply_theme("dark")

    assert export_button.iconSize() == light_export_size
    assert import_button.iconSize() == light_import_size
    assert export_button.icon().isNull() is False
    assert import_button.icon().isNull() is False

    theme.apply_theme("light")

    assert export_button.iconSize() == light_export_size
    assert import_button.iconSize() == light_import_size

    win.close()
