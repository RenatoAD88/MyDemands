from ui_theme import status_color, timing_color


def test_status_color_maps_known_states():
    assert status_color("Concluído") == (210, 242, 220)
    assert status_color("Em espera") == (255, 243, 205)


def test_timing_color_maps_delay_and_default():
    assert timing_color("Em Atraso") == (255, 228, 230)
    assert timing_color("Sem Prazo Definido") == (243, 244, 246)
