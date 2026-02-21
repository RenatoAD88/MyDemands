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
    tomorrow = (date.today() + timedelta(days=1)).strftime("%d/%m/%Y")
    yesterday = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")

    rows = [
        _row("1", Status="Concluído", Prioridade="Alta", Timing="Concluída no Prazo"),
        _row("2", Status="Em andamento", Prioridade="Média", Prazo=today, Timing="Dentro do Prazo"),
        _row("3", Status="Bloqueado", Prioridade="Baixa", Prazo=yesterday, Timing="Em Atraso"),
        _row("4", Status="Não iniciada", Prioridade="Baixa", Prazo=tomorrow, Timing="Concluída antes do Prazo"),
    ]
    service = DashboardMetricsService()
    metrics = service.calculate(rows)

    assert metrics.total_demandas == 4
    assert metrics.concluidas == 1
    assert metrics.concluidas_percentual == 25
    assert metrics.em_andamento == 1
    assert metrics.em_atraso == 1
    assert metrics.canceladas == 0
    assert metrics.por_prioridade == {"Alta": 1, "Média": 1, "Baixa": 2}
    assert metrics.big_numbers["Bloqueado"] == 1
    assert metrics.status_gerais["Dentro do prazo"] == 1
    assert metrics.status_gerais["Concluído antes do prazo"] == 1
    assert metrics.status_gerais["Concluído no prazo"] == 1
    assert metrics.status_gerais["Em atraso"] == 1
    assert [a["badge"] for a in metrics.alertas] == ["Atrasada", "Prazo hoje", "Vencimento próximo"]


def test_metrics_cache_returns_same_object_for_same_fingerprint():
    rows = [_row("1", Status="Concluído")]
    service = DashboardMetricsService()

    first = service.calculate(rows)
    second = service.calculate(list(rows))

    assert first is second
