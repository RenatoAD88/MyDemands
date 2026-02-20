from datetime import date, timedelta

from mydemands.dashboard.metrics_service import DashboardMetricsService


def _row(_id: str, **kwargs):
    base = {
        "_id": _id,
        "ID": _id,
        "Status": "Não iniciada",
        "Prioridade": "Baixa",
        "Prazo": "",
        "Projeto": "Projeto",
        "Descrição": "Demanda",
    }
    base.update(kwargs)
    return base


def test_metrics_calculation_counts_and_alerts():
    today = date.today().strftime("%d/%m/%Y")
    yesterday = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

    rows = [
        _row("1", Status="Concluído", Prioridade="Alta"),
        _row("2", Status="Em andamento", Prioridade="Média", Prazo=today),
        _row("3", Status="Em espera", Prioridade="Baixa", Prazo=yesterday),
    ]
    service = DashboardMetricsService()
    metrics = service.calculate(rows)

    assert metrics.total_demandas == 3
    assert metrics.concluidas == 1
    assert metrics.concluidas_percentual == 33
    assert metrics.em_andamento == 1
    assert metrics.em_atraso == 1
    assert metrics.por_prioridade == {"Alta": 1, "Média": 1, "Baixa": 1}
    assert [a["badge"] for a in metrics.alertas] == ["Atrasada", "Prazo hoje"]


def test_metrics_cache_returns_same_object_for_same_fingerprint():
    rows = [_row("1", Status="Concluído")]
    service = DashboardMetricsService()

    first = service.calculate(rows)
    second = service.calculate(list(rows))

    assert first is second
