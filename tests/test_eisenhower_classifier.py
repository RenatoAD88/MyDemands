from datetime import date

from mydemands.dashboard.eisenhower_classifier import EisenhowerClassifierService


def _row(prioridade: str, urgente: str, timing: str, prazo: str = ""):
    return {
        "Status": "Em andamento",
        "Prioridade": prioridade,
        "É Urgente?": urgente,
        "Timing": timing,
        "Prazo": prazo,
    }


def test_classifier_matrix_combinations_priority_urgent_timing():
    service = EisenhowerClassifierService(today_provider=lambda: date(2026, 2, 10))
    expected_by_priority = {"Alta": "q3", "Média": "q3", "Baixa": "q4"}

    for prioridade, expected_non_urgent in expected_by_priority.items():
        assert service.classify(_row(prioridade, "Não", "Dentro do Prazo")) == expected_non_urgent
        urgent_expected = "q1" if prioridade in {"Alta", "Média"} else "q2"
        assert service.classify(_row(prioridade, "Sim", "Dentro do Prazo")) == urgent_expected
        assert service.classify(_row(prioridade, "Não", "Em Atraso")) == urgent_expected
        assert service.classify(_row(prioridade, "Não", "Dentro do Prazo", "10/02/2026")) == urgent_expected
        assert service.classify(_row(prioridade, "Não", "Sem Prazo Definido")) == expected_non_urgent


def test_classifier_excludes_concluded_and_cancelled():
    service = EisenhowerClassifierService()
    assert service.classify({"Status": "Concluído"}) == "excluded"
    assert service.classify({"Status": "Cancelado"}) == "excluded"


def test_classifier_defaults_for_missing_fields():
    service = EisenhowerClassifierService(today_provider=lambda: date(2026, 2, 10))
    row = {"Status": "Não iniciada", "Prioridade": "", "É Urgente?": "", "Timing": "Dentro do Prazo"}
    assert service.classify(row) == "q3"
