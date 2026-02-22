from validation import validate_payload


def _base_payload(**extra):
    payload = {
        "Descrição": "Demanda",
        "Projeto": "Projeto",
        "Prioridade": "Alta",
        "Prazo": "10/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "R",
        "% Conclusão": "0.25",
        "É Urgente?": "Não",
    }
    payload.update(extra)
    return payload


def test_create_mantem_comportamento_legado_sem_consistencia_global_de_datas():
    out = validate_payload(
        _base_payload(
            Prazo="31/01/2026",
            Status="Concluído",
            **{"Data Conclusão": ""},
            **{"% Conclusão": "1"},
        ),
        mode="create",
    )
    assert out["Prazo"] == "31/01/2026"
    assert out["Status"] == "Concluído"
    assert out["Data Conclusão"] == ""


def test_update_parcial_nao_exige_data_registro_no_payload():
    out = validate_payload({"Prazo": "11/02/2026"}, mode="update")
    assert out["Prazo"] == "11/02/2026"
