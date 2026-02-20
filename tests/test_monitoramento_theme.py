import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from mydemands.dashboard.view import MonitoramentoView

QApplication = qtwidgets.QApplication


def _app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_monitoramento_view_theme_switch_changes_stylesheet():
    _app()
    view = MonitoramentoView()

    view.apply_theme("light")
    light_qss = view.styleSheet()
    assert "#F7F9FC" in light_qss

    view.apply_theme("dark")
    dark_qss = view.styleSheet()
    assert "#0F172A" in dark_qss
    assert dark_qss != light_qss
