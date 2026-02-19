from ui_theme import _read_qss, build_app_stylesheet


def test_build_stylesheet_light_not_empty():
    stylesheet = build_app_stylesheet("light")
    assert isinstance(stylesheet, str)
    assert stylesheet.strip()


def test_build_stylesheet_dark_not_empty():
    stylesheet = build_app_stylesheet("dark")
    assert isinstance(stylesheet, str)
    assert stylesheet.strip()


def test_read_qss_files_exist():
    assert _read_qss("base.qss")
    assert _read_qss("light_colors.qss")
    assert _read_qss("dark_colors.qss")
