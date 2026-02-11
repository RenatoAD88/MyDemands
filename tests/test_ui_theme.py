from ui_theme import APP_STYLESHEET, status_color, timing_color


def test_status_color_maps_known_states():
    assert status_color("Concluído") == (210, 242, 220)
    assert status_color("Em espera") == (255, 243, 205)


def test_timing_color_maps_delay_and_default():
    assert timing_color("Em Atraso") == (255, 228, 230)
    assert timing_color("Sem Prazo Definido") == (243, 244, 246)


def test_stylesheet_has_ergonomic_header_palette():
    assert "QMainWindow { background: #f3f6fb; }" in APP_STYLESHEET
    assert "QTabBar::tab {" in APP_STYLESHEET
    assert "background: #e8eef9;" in APP_STYLESHEET
    assert "QTabBar::tab:selected {" in APP_STYLESHEET
    assert "border: 1px solid #7aa2e3;" in APP_STYLESHEET


def test_stylesheet_has_readable_inputs_and_table():
    assert "QLineEdit, QTextEdit, QComboBox, QDateEdit, QListWidget {" in APP_STYLESHEET
    assert "color: #111827;" in APP_STYLESHEET
    assert "QComboBox QAbstractItemView {" in APP_STYLESHEET
    assert "selection-background-color: #dbeafe;" in APP_STYLESHEET
    assert "selection-color: #0f172a;" in APP_STYLESHEET
    assert "QHeaderView::section {" in APP_STYLESHEET
    assert "background: #dde7f8;" in APP_STYLESHEET


def test_stylesheet_keeps_native_dropdown_arrows_visible():
    assert "QComboBox::down-arrow, QDateEdit::down-arrow {" in APP_STYLESHEET
    block = APP_STYLESHEET.split("QComboBox::down-arrow, QDateEdit::down-arrow {", 1)[1].split("}", 1)[0]
    assert "image: none;" not in block
