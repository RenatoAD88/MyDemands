import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtgui = pytest.importorskip("PySide6.QtGui", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
QApplication = qtwidgets.QApplication
QTableWidget = qtwidgets.QTableWidget
QAbstractItemView = qtwidgets.QAbstractItemView
QColor = qtgui.QColor

from mydemands.services.theme_service import ThemeService
from ui_theme import apply_dynamic_selection_style, best_text_color, build_app_stylesheet, luminance, status_color, timing_color


def test_status_color_maps_known_states():
    assert status_color("Concluído") == (210, 242, 220)
    assert status_color("Não iniciada") == (255, 228, 230)
    assert status_color("Não Iniciado") == (255, 228, 230)
    assert status_color("Requer revisão") == (237, 233, 254)
    assert status_color("Bloqueado") == (255, 243, 205)


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


def test_dark_stylesheet_has_high_contrast_table_and_header_colors():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    stylesheet = build_app_stylesheet("dark")
    assert "QTableView {" in stylesheet
    assert "color: #EAEAEA;" in stylesheet
    assert "background-color: #1E1E1E;" in stylesheet
    assert "QTableView::item:selected {" in stylesheet
    assert "background-color: #2D3E50;" in stylesheet
    assert "color: #FFFFFF;" in stylesheet
    assert "QHeaderView::section {" in stylesheet
    assert "background: #2A2A2A;" in stylesheet


def test_luminance_detects_light_and_dark_backgrounds():
    assert luminance(QColor(255, 255, 255)) > 0.5
    assert luminance(QColor(20, 20, 20)) <= 0.5


def test_best_text_color_prefers_high_contrast_pair():
    assert best_text_color(QColor("#101010")).name() == QColor("white").name()
    assert best_text_color(QColor("#f0f4ff")).name() == QColor("black").name()


def test_apply_dynamic_selection_style_sets_rows_selection_and_qss():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    table = QTableWidget(0, 2)
    table.setStyleSheet("QTableWidget { border: 1px solid #000; }")
    apply_dynamic_selection_style(table)

    assert table.selectionBehavior() == QAbstractItemView.SelectRows
    qss = table.styleSheet()
    assert "/* dynamic-table-selection:start */" in qss
    assert "QTableWidget::item:selected" in qss


def test_apply_dynamic_selection_style_replaces_previous_dynamic_block():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    table = QTableWidget(0, 2)
    apply_dynamic_selection_style(table)
    first = table.styleSheet()
    apply_dynamic_selection_style(table)
    second = table.styleSheet()

    assert second.count("/* dynamic-table-selection:start */") == 1
    assert len(second) >= len(first)
