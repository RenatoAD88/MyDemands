import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from mydemands.dashboard.metrics_service import DashboardMetrics
from mydemands.dashboard.view import MonitoramentoView

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
        alertas=[],
    )


def test_cards_keep_minimum_height_with_zero_values():
    _app()
    view = MonitoramentoView()
    view.update_metrics(_empty_metrics())

    assert view._cards["big_numbers"].minimumHeight() >= 110
    assert view._cards["progresso"].minimumHeight() >= 110
    assert view.progress_bar.value() == 0
    assert view.progress_percent_label.text() == "0%"


def test_layout_does_not_collapse_without_data():
    _app()
    view = MonitoramentoView()
    view.update_metrics(_empty_metrics())

    assert view._cards["graficos"].minimumHeight() >= 280
    assert view._cards["alertas"].minimumHeight() >= 100
    assert view.done_subtitle.text() == "Nenhuma demanda concluída ainda"


def test_empty_dataset_shows_placeholders():
    _app()
    view = MonitoramentoView()
    view.update_metrics(_empty_metrics())

    assert view.donut.empty_placeholder == "Sem dados suficientes"
    assert view.bars.empty_placeholder == "Sem dados suficientes"
    assert view.legend_status.text() == "Sem dados"

    placeholders = [
        lbl.text()
        for lbl in view.findChildren(QLabel)
        if lbl.objectName() == "metricPlaceholder"
    ]
    assert "Sem demandas atrasadas, para hoje ou com vencimento próximo." in placeholders


def test_typography_hierarchy_is_applied_in_stylesheet():
    _app()
    view = MonitoramentoView()
    qss = view.styleSheet()

    assert "QLabel#metricTitle" in qss
    assert "QLabel#sectionTitle" in qss
    assert "QLabel#metricValue" in qss
    assert "font-size: 32px" in qss
    assert "QLabel#progressPercent" in qss
