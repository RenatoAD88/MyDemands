import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
QApplication = qtwidgets.QApplication

from mydemands.services.theme_service import ThemeService
from ui_theme import build_app_stylesheet, status_color, timing_color


def test_status_color_maps_known_states():
    assert status_color("Concluído") == (210, 242, 220)
    assert status_color("Não iniciada") == (255, 228, 230)
    assert status_color("Não Iniciado") == (255, 228, 230)
    assert status_color("Requer revisão") == (237, 233, 254)
    assert status_color("Em espera") == (255, 243, 205)


def test_timing_color_maps_delay_and_default():
    assert timing_color("Em Atraso") == (255, 228, 230)
    assert timing_color("Sem Prazo Definido") == (243, 244, 246)


def test_stylesheet_has_ergonomic_header_palette():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    stylesheet = build_app_stylesheet("light")
    assert "QMainWindow { background: #f3f6fb; }" in stylesheet
    assert "QTabBar::tab {" in stylesheet
    assert "background: #e8eef9;" in stylesheet
    assert "QTabBar::tab:selected {" in stylesheet
    assert "border-color: #7aa2e3;" in stylesheet


def test_stylesheet_has_readable_inputs_and_table():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    stylesheet = build_app_stylesheet("light")
    assert "QLineEdit, QTextEdit, QComboBox, QDateEdit, QListWidget {" in stylesheet
    assert "color: #111827;" in stylesheet
    assert "QComboBox QAbstractItemView {" in stylesheet
    assert "selection-background-color: #dbeafe;" in stylesheet
    assert "selection-color: #0f172a;" in stylesheet
    assert "QHeaderView::section {" in stylesheet
    assert "background: #dde7f8;" in stylesheet


def test_stylesheet_keeps_native_dropdown_arrows_visible():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    stylesheet = build_app_stylesheet("light")
    assert "QComboBox::down-arrow, QDateEdit::down-arrow {" in stylesheet
    block = stylesheet.split("QComboBox::down-arrow, QDateEdit::down-arrow {", 1)[1].split("}", 1)[0]
    assert "image: none;" not in block


def test_stylesheet_checkbox_indicator_has_explicit_high_contrast_checkmark():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    stylesheet = build_app_stylesheet("light")
    assert "QCheckBox::indicator:checked {" in stylesheet
    assert "background: #1d4ed8;" in stylesheet
    assert "stroke='%23ffffff'" in stylesheet
    assert "QCheckBox::indicator:disabled {" in stylesheet


def test_dark_theme_uses_same_sizing_tokens_as_light():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    light = build_app_stylesheet("light")
    dark = build_app_stylesheet("dark")
    shared_tokens = [
        "font-size: 13px;",
        "padding: 8px 14px;",
        "padding: 6px 12px;",
        "min-height: 26px;",
        "width: 16px;",
        "height: 16px;",
    ]
    for token in shared_tokens:
        assert token in light
        assert token in dark


def test_build_stylesheet_returns_string():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    css_light = build_app_stylesheet("light")
    css_dark = build_app_stylesheet("dark")
    assert isinstance(css_light, str)
    assert isinstance(css_dark, str)
    assert len(css_light) > 0
    assert len(css_dark) > 0


def test_theme_service_applies_stylesheet_without_exception():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    service = ThemeService(app)
    service.apply_theme("light")
    service.apply_theme("dark")
    assert isinstance(app.styleSheet(), str)
    assert len(app.styleSheet()) > 0


def test_build_stylesheet_after_qapplication_does_not_raise():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    stylesheet = build_app_stylesheet("light")
    assert isinstance(stylesheet, str)
    assert stylesheet
