from ui_theme import _read_qss


def test_styles_package_importable():
    import mydemands.ui.styles

    assert mydemands.ui.styles is not None


def test_read_qss_works():
    assert len(_read_qss("base.qss")) > 0
    assert len(_read_qss("light_colors.qss")) > 0
    assert len(_read_qss("dark_colors.qss")) > 0
