from form_rules import required_fields


def test_required_fields_detects_core_missing():
    missing = required_fields({"Descrição": "", "Prioridade": "", "Status": "", "Responsável": ""}, prazo_count=0)
    assert "Descrição" in missing
    assert "Prazo" in missing


def test_required_fields_requires_conclusion_when_concluded():
    payload = {
        "Descrição": "x",
        "Prioridade": "Alta",
        "Status": "Concluído",
        "Responsável": "R",
        "% Conclusão": "100% - Concluído",
        "Data Conclusão": "",
    }
    missing = required_fields(payload, prazo_count=1)
    assert "Data Conclusão" in missing
