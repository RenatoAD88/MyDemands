from datetime import date

import pytest

from csv_store import CsvStore
from validation import ValidationError


def _base_payload(**overrides):
    payload = {
        "Descrição": "Demanda",
        "Projeto": "Projeto",
        "Prioridade": "Alta",
        "Prazo": date.today().strftime("%d/%m/%Y"),
        "Data de Registro": date.today().strftime("%d/%m/%Y"),
        "Status": "Em andamento",
        "Data Conclusão": "",
        "Responsável": "Pessoa",
        "% Conclusão": "0.5",
    }
    payload.update(overrides)
    return payload


def test_status_dropdowns_include_cancelado():
    app_source = open("app.py", "r", encoding="utf-8").read()
    assert 'STATUS_EDIT_OPTIONS = [' in app_source
    assert 'TAB3_STATUS_FILTER_OPTIONS = [' in app_source
    assert '"Cancelado"' in app_source


def test_cancelled_status_resets_percent_and_conclusion_date(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add(_base_payload())

    store.update(_id, {"Status": "Cancelado", "% Conclusão": "0.75", "Data Conclusão": "01/01/2026"})

    row = store.get(_id)
    assert row is not None
    assert row.data["Status"] == "Cancelado"
    assert row.data["% Conclusão"] == "0"
    assert row.data["Data Conclusão"] == ""


def test_concluded_demand_cannot_be_cancelled(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add(
        _base_payload(
            Status="Concluído",
            **{"Data Conclusão": date.today().strftime("%d/%m/%Y"), "% Conclusão": "1"},
        )
    )

    with pytest.raises(ValidationError):
        store.update(_id, {"Status": "Cancelado"})


def test_cancelled_demands_are_listed_only_in_cancelled_tab_source(tmp_path):
    store = CsvStore(str(tmp_path))
    cancelled_id = store.add(_base_payload(Status="Cancelado", **{"% Conclusão": "0"}))
    concluded_id = store.add(
        _base_payload(
            Status="Concluído",
            **{"Data Conclusão": date.today().strftime("%d/%m/%Y"), "% Conclusão": "1"},
        )
    )

    pending_ids = {row["_id"] for row in store.tab_pending_all()}
    concluded_ids = {row["_id"] for row in store.tab_concluidas_all()}
    cancelled_ids = {row["_id"] for row in store.tab_canceladas_all()}

    assert cancelled_id not in pending_ids
    assert cancelled_id not in concluded_ids
    assert cancelled_id in cancelled_ids
    assert concluded_id in concluded_ids
