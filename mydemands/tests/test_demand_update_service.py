from mydemands.dashboard.demand_update_service import DemandUpdateService


def test_update_ignora_falha_no_after_update_e_persiste_update():
    calls = {"updated": None, "after": 0}

    def _update_callable(demand_id, changes):
        calls["updated"] = (demand_id, changes)

    def _after_update():
        calls["after"] += 1
        raise RuntimeError("falha simulada")

    service = DemandUpdateService(_update_callable, _after_update)

    service.update("abc-123", {"Data de Registro": "03/02/2026"})

    assert calls["updated"] == ("abc-123", {"Data de Registro": "03/02/2026"})
    assert calls["after"] == 1
