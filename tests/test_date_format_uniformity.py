from __future__ import annotations

import pytest

from csv_store import CsvStore
from date_field_service import DateFieldError, format_ui_date, normalize_date_for_storage, parse_ui_date
from validation import ValidationError, validate_payload


def _base_payload(**extra):
    payload = {
        "Descrição": "Demanda",
        "Projeto": "Projeto",
        "Prioridade": "Alta",
        "Prazo": "30/12/2025",
        "Data de Registro": "01/12/2025",
        "Status": "Em andamento",
        "Responsável": "R",
        "% Conclusão": "0.25",
        "É Urgente?": "Não",
        "Data Conclusão": "",
    }
    payload.update(extra)
    return payload


def test_parse_ui_date_accepts_valid_br_dates():
    assert format_ui_date(parse_ui_date("30/12/2025")) == "30/12/2025"
    assert format_ui_date(parse_ui_date("01/01/2025")) == "01/01/2025"


@pytest.mark.parametrize("raw", ["01/01/2000", "07/03/2026", "30/12/2025"])
def test_parse_ui_date_accepts_reported_valid_examples(raw):
    assert format_ui_date(parse_ui_date(raw)) == raw


@pytest.mark.parametrize("raw", ["30-12-2025", "2025-12-30", "30/12/25", "1/1/2025"])
def test_parse_ui_date_rejects_non_ddmmyyyy(raw):
    with pytest.raises(DateFieldError):
        parse_ui_date(raw)


@pytest.mark.parametrize(
    ("raw", "should_pass"),
    [
        ("31/02/2025", False),
        ("29/02/2024", True),
        ("29/02/2025", False),
    ],
)
def test_parse_ui_date_validates_calendar_dates(raw, should_pass):
    if should_pass:
        assert normalize_date_for_storage(parse_ui_date(raw)) == raw
    else:
        with pytest.raises(DateFieldError):
            parse_ui_date(raw)


def test_validation_accepts_30122025():
    out = validate_payload(_base_payload(**{"Data de Registro": "30/12/2025"}), mode="create")
    assert out["Data de Registro"] == "30/12/2025"


@pytest.mark.parametrize("raw", ["30-12-2025", "2025-12-30", "30/12/25"])
def test_validation_rejects_invalid_date_formats(raw):
    with pytest.raises(ValidationError):
        validate_payload(_base_payload(**{"Data de Registro": raw}), mode="create")


def test_csv_persistence_and_reload_keep_ddmmyyyy_for_all_date_fields(tmp_path):
    store = CsvStore(str(tmp_path))
    demand_id = store.add(
        _base_payload(
            **{
                "Data de Registro": "30/12/2025",
                "Prazo": "30/12/2025",
                "Status": "Concluído",
                "% Conclusão": "1",
                "Data Conclusão": "31/12/2025",
            }
        )
    )

    reloaded = CsvStore(str(tmp_path))
    row = reloaded.get(demand_id)
    assert row is not None
    assert row.data["Data de Registro"] == "30/12/2025"
    assert row.data["Prazo"] == "30/12/2025"
    assert row.data["Data Conclusão"] == "31/12/2025"


def test_single_error_message_for_same_invalid_date():
    with pytest.raises(ValidationError) as exc:
        validate_payload(_base_payload(**{"Data de Registro": "2025-12-30"}), mode="create")
    message = str(exc.value)
    assert message.count("Data de Registro") == 1
    assert "DD/MM/AAAA" in message
