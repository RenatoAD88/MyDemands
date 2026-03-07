from __future__ import annotations

from csv_store import CsvStore, DemandRow
from mydemands.dashboard.demand_update_service import DemandUpdateService
from validation import ValidationError


def _payload(**extra):
    payload = {
        "É Urgente?": "Não",
        "Status": "Em andamento",
        "Prioridade": "Média",
        "Data de Registro": "01/02/2026",
        "Prazo": "10/02/2026",
        "Data Conclusão": "",
        "Projeto": "Projeto Registro",
        "Descrição": "Linha",
        "Comentário": "",
        "ID Azure": "AZ-1",
        "% Conclusão": "0.25",
        "Responsável": "Equipe",
        "Reportar?": "Não",
        "Nome": "Fulano",
        "Time/Função": "Dev",
    }
    payload.update(extra)
    return payload


def test_rebuild_indice_apos_load(tmp_path):
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload())
    store.load()

    state = store.describe_lookup_state(demand_id)
    assert state["id_exists_in_index"] is True
    assert store.get(demand_id) is not None


def test_rebuild_indice_apos_save(tmp_path):
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload())
    store._rows_by_id = {}

    store.save()

    assert store.get(demand_id) is not None


def test_rebuild_indice_apos_import_replace_e_merge(tmp_path):
    store = CsvStore(str(tmp_path))
    old_id = store.add(_payload())
    imported = DemandRow(_id="novo-id", data={**store.get(old_id).data, "_id": "novo-id", "ID": "100"})

    store.replace_with_rows([imported])
    assert store.get("novo-id") is not None
    assert store.get(old_id) is None

    merged_row = DemandRow(_id="merge-id", data={**imported.data, "_id": "merge-id", "ID": "101"})
    store.merge_with_rows([merged_row])

    rows = store.build_view()
    assert len(rows) == 2
    assert all(store.get(r["_id"]) is not None for r in rows)


def test_rebuild_indice_apos_exclusao(tmp_path):
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload())

    assert store.delete_by_id(demand_id) is True
    state = store.describe_lookup_state(demand_id)
    assert state["id_exists_in_index"] is False
    assert store.get(demand_id) is None


def test_falha_controlada_apenas_quando_id_nao_existe():
    row = DemandRow(_id="ok-id", data={"Data de Registro": "01/02/2026"})
    service = DemandUpdateService(lambda *_args: None, lambda _id: row if _id == "ok-id" else None)

    service.update("ok-id", {"Data de Registro": "02/02/2026"})

    try:
        service.update("inexistente", {"Data de Registro": "02/02/2026"})
    except ValidationError as exc:
        assert "Não foi possível localizar a demanda selecionada" in str(exc)
    else:
        raise AssertionError("Era esperado ValidationError para ID inexistente")


def test_sincronizacao_dataset_mestre_e_visoes_derivadas(tmp_path):
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload(Status="Em andamento", **{"Data Conclusão": "", "% Conclusão": "0.5"}))

    assert any(r["_id"] == demand_id for r in store.tab_pending_all())
    assert not any(r["_id"] == demand_id for r in store.tab_concluidas_all())

    store.update(demand_id, {"Status": "Concluído", "Data Conclusão": "10/02/2026", "% Conclusão": "1"})

    assert not any(r["_id"] == demand_id for r in store.tab_pending_all())
    assert any(r["_id"] == demand_id for r in store.tab_concluidas_all())
