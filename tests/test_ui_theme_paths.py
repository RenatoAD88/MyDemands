from mydemands.ui.stylesheets import BASE_QSS, DARK_COLORS_QSS, LIGHT_COLORS_QSS


def test_dark_and_light_colors_contain_only_color_tokens():
    assert "min-height" not in LIGHT_COLORS_QSS
    assert "min-height" not in DARK_COLORS_QSS
    assert "padding: 8px 14px;" not in LIGHT_COLORS_QSS
    assert "padding: 8px 14px;" not in DARK_COLORS_QSS


def test_base_contains_shared_sizing_tokens():
    assert "font-size: 13px;" in BASE_QSS
    assert "min-height: 26px;" in BASE_QSS
    assert "min-height: 28px;" in BASE_QSS
