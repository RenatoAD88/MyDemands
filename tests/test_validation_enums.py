import pytest
from validation import validate_payload, ValidationError


def test_status_canonicalization_accepts_variants():
    # Aceita variação antiga e normaliza para canônico novo
    out = validate_payload({"Status": "Não Iniciada"}, mode="update")
    assert out["Status"] == "Não iniciada"

    out = validate_payload({"Status": "Em Andamento"}, mode="update")
    assert out["Status"] == "Em andamento"

    out = validate_payload({"Status": "Requer Revisão"}, mode="update")
    assert out["Status"] == "Requer revisão"

    out = validate_payload({"Status": "Concluído"}, mode="update")
    assert out["Status"] == "Concluído"


def test_prioridade_canonicalization_accepts_media_without_accent():
    out = validate_payload({"Prioridade": "media"}, mode="update")
    assert out["Prioridade"] == "Média"


def test_yesno_enums_are_enforced():
    out = validate_payload({"É Urgente?": "Sim"}, mode="update")
    assert out["É Urgente?"] == "Sim"

    out = validate_payload({"Reportar?": "Não"}, mode="update")
    assert out["Reportar?"] == "Não"

    with pytest.raises(ValidationError):
        validate_payload({"É Urgente?": "Talvez"}, mode="update")
