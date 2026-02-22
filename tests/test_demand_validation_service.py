import pytest

from validation import DemandValidationService, ValidationError, validate_payload


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


def test_prazo_menor_que_registro_bloqueia_com_mensagem_amigavel():
    with pytest.raises(ValidationError, match=DemandValidationService.PRAZO_LT_REGISTRO_MSG):
        validate_payload(_base_payload(Prazo="31/01/2026"), mode="create")


def test_conclusao_menor_que_registro_bloqueia_com_mensagem_amigavel():
    with pytest.raises(ValidationError, match=DemandValidationService.CONCLUSAO_LT_REGISTRO_MSG):
        validate_payload(_base_payload(Status="Concluído", **{"Data Conclusão": "31/01/2026"}, **{"% Conclusão": "1"}), mode="create")


def test_concluido_sem_data_conclusao_bloqueia():
    with pytest.raises(ValidationError, match=DemandValidationService.CONCLUIDO_SEM_CONCLUSAO_MSG):
        validate_payload(_base_payload(Status="Concluído", **{"Data Conclusão": ""}, **{"% Conclusão": "1"}), mode="create")


def test_cancelado_com_data_conclusao_bloqueia():
    with pytest.raises(ValidationError, match=DemandValidationService.CANCELADO_COM_CONCLUSAO_MSG):
        validate_payload(_base_payload(Status="Cancelado", **{"Data Conclusão": "02/02/2026"}, **{"% Conclusão": "0"}), mode="create")


def test_prazo_vazio_e_permitido():
    out = validate_payload(_base_payload(Prazo=""), mode="create")
    assert out["Prazo"] == ""


def test_update_parcial_nao_exige_data_registro_no_payload():
    out = validate_payload({"Prazo": "11/02/2026"}, mode="update")
    assert out["Prazo"] == "11/02/2026"
