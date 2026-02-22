import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from mydemands.dashboard.metrics_service import DashboardMetrics
from mydemands.dashboard.view import MonitoramentoView, TimingBarsWidget

QApplication = qtwidgets.QApplication
QLabel = qtwidgets.QLabel


def _app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _empty_metrics() -> DashboardMetrics:
    return DashboardMetrics(
        total_demandas=0,
        concluidas=0,
        concluidas_percentual=0,
        em_atraso=0,
        em_andamento=0,
        canceladas=0,
        por_status={},
        por_prioridade={"Alta": 0, "Média": 0, "Baixa": 0},
        status_gerais={"Dentro do prazo": 0, "Concluído antes do prazo": 0, "Concluído no prazo": 0, "Concluída com atraso": 0, "Em atraso": 0},
        big_numbers={"Total de Demandas": 0, "Não iniciado": 0, "Em andamento": 0, "Bloqueado": 0, "Requer revisão": 0, "Cancelado": 0, "Concluído": 0},
        alertas=[],
    )


def test_cards_keep_minimum_height_with_zero_values():
    _app()
    view = MonitoramentoView()
    view.update_metrics(_empty_metrics())

    assert view._cards["big_numbers"].minimumHeight() >= 110
    assert view._cards["progresso"].minimumHeight() >= 110
    assert view._cards["graficos"].minimumHeight() >= 300
    assert view.progress_bar.value() == 0
    assert view.progress_percent_label.text() == "0%"


def test_por_status_section_removed_and_grouped_cards_side_by_side():
    _app()
    view = MonitoramentoView()

    section_titles = [lbl.text().lower() for lbl in view.findChildren(QLabel) if lbl.objectName() == "sectionTitle"]
    assert "por status" not in section_titles
    assert "status gerais" in section_titles
    assert "por prioridade" in section_titles

    assert view.status_gerais_card.minimumHeight() == view.priority_card.minimumHeight()


def test_prioridade_uses_donut_with_expected_colors_and_placeholder():
    _app()
    view = MonitoramentoView()
    view.update_metrics(_empty_metrics())

    assert view.priority_pie.empty_placeholder == "Sem dados"
    assert view.priority_pie.colors["Alta"] == "#EF4444"
    assert view.priority_pie.colors["Média"] == "#FACC15"
    assert view.priority_pie.colors["Baixa"] == "#22C55E"
    assert "Alta:" in view.priority_legend.text()




def test_status_gerais_labels_render_full_text_with_wrap_support():
    _app()
    view = MonitoramentoView()

    bars = view.status_gerais_bars
    assert bars.order == [
        "Dentro do prazo",
        "Concluído antes do prazo",
        "Concluído no prazo",
        "Concluída com atraso",
        "Em atraso",
    ]
    assert bars.label_height >= 56
    assert bars.footer_min_height >= bars.label_height
    assert bars.min_column_width >= 110
    assert bars.label_text_flags & qtcore.Qt.TextWordWrap


def test_status_gerais_labels_have_reserved_footer_without_elide_or_crop():
    _app()
    view = MonitoramentoView()
    bars = view.status_gerais_bars
    bars.resize(760, 260)
    bars.show()
    _app().processEvents()

    assert bars.height() >= bars.minimumHeight()
    assert bars.label_font_size <= 11

    font = bars.font()
    font.setPointSize(bars.label_font_size)
    metrics = qtwidgets.QFontMetrics(font)
    expected_multiline_height = metrics.boundingRect(
        qtcore.QRect(0, 0, bars.min_column_width, 400),
        bars.label_text_flags,
        "Concluído antes do prazo",
    ).height()
    assert expected_multiline_height <= bars.footer_min_height

    bars.set_data(
        {
            "Dentro do prazo": 9,
            "Concluído antes do prazo": 7,
            "Concluído no prazo": 5,
            "Concluída com atraso": 3,
            "Em atraso": 1,
        }
    )
    bars.repaint()
    _app().processEvents()

    assert set(bars._last_label_rects.keys()) == set(bars.order)
    for label in bars.order:
        rect = bars._last_label_rects[label]
        assert rect.bottom() <= bars.rect().adjusted(14, 14, -14, -10).bottom()

        wrapped_height = metrics.boundingRect(
            qtcore.QRect(0, 0, rect.width(), 400),
            bars.label_text_flags,
            label,
        ).height()
        assert wrapped_height <= rect.height()


def test_por_prioridade_uses_reduced_scale_for_chart():
    _app()
    view = MonitoramentoView()

    assert view.priority_pie.chart_scale == pytest.approx(0.9)


def test_por_prioridade_legend_shows_percentage_when_data_exists():
    _app()
    view = MonitoramentoView()
    metrics = _empty_metrics()
    metrics.por_prioridade = {"Alta": 2, "Média": 1, "Baixa": 1}
    view.update_metrics(metrics)

    legend = view.priority_legend.text()
    assert "Alta:" in legend
    assert "50%" in legend


def test_por_prioridade_placeholder_when_empty_data():
    _app()
    view = MonitoramentoView()
    view.update_metrics(_empty_metrics())

    assert sum(view.priority_pie.data.values()) == 0


def test_por_prioridade_keeps_donut_and_legend_centered():
    _app()
    view = MonitoramentoView()

    layout = view.priority_card.layout()
    assert layout.itemAt(2).spacerItem() is not None
    assert layout.itemAt(5).spacerItem() is not None
    assert view.priority_legend.alignment() == qtcore.Qt.AlignCenter


def test_status_gerais_uses_expected_palette():
    _app()
    view = MonitoramentoView()

    assert TimingBarsWidget.COLOR_MAP["Dentro do prazo"] == "#1E3A8A"
    assert TimingBarsWidget.COLOR_MAP["Concluído antes do prazo"] == "#1D4ED8"
    assert TimingBarsWidget.COLOR_MAP["Concluído no prazo"] == "#3B82F6"
    assert TimingBarsWidget.COLOR_MAP["Concluída com atraso"] == "#93C5FD"
    assert TimingBarsWidget.COLOR_MAP["Em atraso"] == "#EF4444"
    assert view.status_gerais_bars.min_bar_height >= 2


def test_alertas_columns_order_and_empty_state():
    _app()
    view = MonitoramentoView()
    view.update_metrics(_empty_metrics())

    assert view.alerts_empty.text() == "Nenhuma demanda em atraso."
    headers = [view.alerts_table.horizontalHeaderItem(i).text() for i in range(view.alerts_table.columnCount())]
    assert headers == [
        "ID",
        "É Urgente",
        "Status",
        "Timing",
        "Prioridade",
        "Data de Registro",
        "Prazo",
        "Projeto",
        "Descrição",
        "Comentário",
        "Num Controle",
        "% Conclusão",
        "Responsável",
        "Reportar?",
        "Nome",
        "Time/Função",
    ]
    assert "Ações" not in headers
    assert view.alerts_config_button.text() == "Configurar colunas"
    assert view.alerts_restore_button.text() == "Restaurar padrão"


def test_monitoramento_has_no_decorative_icons_in_headers():
    _app()
    view = MonitoramentoView()
    section_titles = [lbl.text() for lbl in view.findChildren(QLabel) if lbl.objectName() == "sectionTitle"]
    assert "Dados Gerais" in section_titles
    assert "Status Gerais" in section_titles
    assert all("◉" not in s and "◎" not in s and "▤" not in s for s in section_titles)


def test_alertas_table_resizes_columns_to_content():
    _app()
    view = MonitoramentoView()

    header = view.alerts_table.horizontalHeader()
    assert header.sectionResizeMode(0) == qtwidgets.QHeaderView.Interactive
    assert header.stretchLastSection() is True
