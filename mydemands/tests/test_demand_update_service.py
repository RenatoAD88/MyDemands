from csv_store import DemandRow
from validation import ValidationError
from mydemands.dashboard.demand_update_service import DemandUpdateService


def test_update_ignora_falha_no_after_update_e_persiste_update():
    calls = {"updated": None, "after": 0}
    row = DemandRow(_id="abc-123", data={"Data de Registro": "01/02/2026"})

    def _update_callable(demand_id, changes):
        calls["updated"] = (demand_id, changes)

    def _get_callable(demand_id):
        return row if demand_id == row._id else None

    def _after_update():
        calls["after"] += 1
        raise RuntimeError("falha simulada")

    service = DemandUpdateService(_update_callable, _get_callable, _after_update)

    result = service.update("abc-123", {"data_registro": "03/02/2026"})

    assert calls["updated"] == ("abc-123", {"Data de Registro": "03/02/2026"})
    assert calls["after"] == 1
    assert result["ok"] is True


def test_update_retorna_erro_amigavel_quando_id_nao_existe():
    service = DemandUpdateService(lambda *_args: None, lambda _id: None)

    try:
        service.update("id-inexistente", {"Data de Registro": "03/02/2026"})
    except ValidationError as exc:
        assert "Não foi possível localizar a demanda selecionada" in str(exc)
    else:
        raise AssertionError("Era esperado ValidationError para ID inexistente")
