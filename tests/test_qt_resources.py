from ui_theme import build_app_stylesheet


def test_build_stylesheet_light_not_empty():
    stylesheet = build_app_stylesheet("light")
    assert isinstance(stylesheet, str)
    assert stylesheet.strip()


def test_build_stylesheet_dark_not_empty():
    stylesheet = build_app_stylesheet("dark")
    assert isinstance(stylesheet, str)
    assert stylesheet.strip()


def test_stylesheets_are_embedded_and_do_not_require_qss_files():
    assert "mydemands/ui/styles" not in build_app_stylesheet("light")
