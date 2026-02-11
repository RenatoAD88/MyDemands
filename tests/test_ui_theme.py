from ui_theme import APP_STYLESHEET, status_color, timing_color


def test_status_color_maps_known_states():
    assert status_color("Concluído") == (210, 242, 220)
    assert status_color("Em espera") == (255, 243, 205)


def test_timing_color_maps_delay_and_default():
    assert timing_color("Em Atraso") == (255, 228, 230)
    assert timing_color("Sem Prazo Definido") == (243, 244, 246)


def test_stylesheet_uses_black_text_and_black_borders():
    assert "QWidget { font-size: 13px; color: #000000; }" in APP_STYLESHEET
    assert "border: 1px solid #000000" in APP_STYLESHEET
