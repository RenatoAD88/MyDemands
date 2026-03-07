from __future__ import annotations

import csv

import pytest

from csv_store import CsvStore, DELIMITER
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


def test_data_registro_regra_prazo_nao_pode_ser_anterior(tmp_path):
    store = CsvStore(str(tmp_path))

    with pytest.raises(ValidationError, match="prazo .* anterior"):
        store.add(_payload(**{"Data de Registro": "15/02/2026", "Prazo": "10/02/2026"}))


def test_data_registro_persistencia_csv_e_recarregamento(tmp_path):
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload())
    store.update(demand_id, {"Data de Registro": "03/02/2026"})

    reloaded = CsvStore(str(tmp_path))
    assert reloaded.get(demand_id).data["Data de Registro"] == "03/02/2026"

    with open(reloaded.csv_path, "rb") as f:
        raw = f.read()
    plain = reloaded._decrypt_bytes(raw).decode("utf-8")
    rows = list(csv.DictReader(plain.splitlines(), delimiter=DELIMITER))
    assert rows[0]["Data de Registro"] == "03/02/2026"


def test_data_registro_backup_restore_preserva_valor(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMANDAS_APP_KEY", "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=")
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src = CsvStore(str(src_dir))
    demand_id = src.add(_payload(**{"Data de Registro": "08/02/2026"}))
    backup_path = tmp_path / "bkp.csv"
    src.export_encrypted_backup_csv(str(backup_path), team_control_payload={})

    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    dst = CsvStore(str(dst_dir))
    dst.import_encrypted_backup_csv(str(backup_path))

    restored = dst.build_view()
    assert len(restored) == 1
    assert restored[0]["Data de Registro"] == "08/02/2026"
    assert dst.get(restored[0]["_id"]).data["ID"] == "1"
    assert demand_id != restored[0]["_id"]
