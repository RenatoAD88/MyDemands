from mydemands.ui.stylesheets import BASE_QSS, DARK_COLORS_QSS, LIGHT_COLORS_QSS
from ui_theme import build_app_stylesheet


def test_embedded_stylesheets_are_available_in_code():
    assert "QWidget" in BASE_QSS
    assert "QTabBar::tab" in BASE_QSS
    assert "#f3f6fb" in LIGHT_COLORS_QSS
    assert "#111827" in DARK_COLORS_QSS


def test_build_stylesheet_light_dark_returns_text():
    light_css = build_app_stylesheet("light")
    dark_css = build_app_stylesheet("dark")

    assert isinstance(light_css, str)
    assert isinstance(dark_css, str)
    assert "font-size: 13px;" in light_css
    assert "background: #f3f6fb;" in light_css
    assert "background: #111827;" in dark_css
