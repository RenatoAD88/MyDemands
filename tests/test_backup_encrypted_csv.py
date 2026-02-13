from csv_store import CsvStore


def _payload():
    return {
        "É Urgente?": "Não",
        "Status": "Não iniciada",
        "Prioridade": "Média",
        "Data de Registro": "01/01/2026",
        "Prazo": "10/01/2026",
        "Data Conclusão": "",
        "Projeto": "Projeto Backup",
        "Descrição": "Linha de teste",
        "ID Azure": "AZ-BKP-1",
        "% Conclusão": "0",
        "Responsável": "Equipe",
        "Reportar?": "Não",
        "Nome": "Fulano",
        "Time/Função": "Dev",
    }


def test_export_encrypted_backup_contains_no_plain_content(tmp_path):
    store = CsvStore(str(tmp_path))
    store.add(_payload())

    bkp_path = tmp_path / "BKP_RAD20260212223009.csv"
    team_payload = {"periods": {"2026-02": {"sections": []}}}
    store.export_encrypted_backup_csv(str(bkp_path), team_payload)

    raw = bkp_path.read_bytes()
    assert b"Projeto Backup" not in raw
    assert raw.startswith(b"MYDEMANDS_ENC_V1\n")


def test_restore_encrypted_backup_replaces_data_and_returns_team_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMANDAS_APP_KEY", "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=")

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    source = CsvStore(str(src_dir))
    source.add(_payload())
    team_payload = {"periods": {"2026-02": {"sections": [{"id": "s1", "name": "Time A", "members": []}]}}}
    bkp_path = tmp_path / "BKP_RAD20260212223009.csv"
    source.export_encrypted_backup_csv(str(bkp_path), team_payload)

    dst_dir = tmp_path / "dst"
    dst_dir.mkdir()
    target = CsvStore(str(dst_dir))
    target.add({**_payload(), "Projeto": "Outro"})

    restored_team_payload = target.import_encrypted_backup_csv(str(bkp_path))

    rows = target.build_view()
    assert len(rows) == 1
    assert rows[0]["Projeto"] == "Projeto Backup"
    assert restored_team_payload == team_payload
