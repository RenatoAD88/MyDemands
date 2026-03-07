from csv_store import CsvStore


def _payload():
    return {
        "É Urgente?": "Não",
        "Status": "Não iniciada",
        "Prioridade": "Média",
        "Data de Registro": "01/01/2025",
        "Prazo": "10/01/2025",
        "Data Conclusão": "",
        "Projeto": "Projeto Secreto",
        "Descrição": "Dados sensíveis",
        "ID Azure": "AZ-ENC-1",
        "% Conclusão": "0",
        "Responsável": "Equipe",
        "Reportar?": "Não",
        "Nome": "Fulano",
        "Time/Função": "Dev",
    }


def test_data_csv_is_encrypted_at_rest_and_readable_by_app(tmp_path):
    store = CsvStore(str(tmp_path))
    store.add(_payload())

    raw = (tmp_path / "data.csv").read_bytes()
    assert b"_id;" not in raw
    assert b"Projeto Secreto" not in raw

    # A aplicação consegue abrir normalmente o mesmo arquivo criptografado.
    reopened = CsvStore(str(tmp_path))
    rows = reopened.build_view()
    assert len(rows) == 1
    assert rows[0]["Projeto"] == "Projeto Secreto"


def test_creates_local_key_file_for_encryption(tmp_path):
    CsvStore(str(tmp_path))
    key_path = tmp_path / ".demandas.key"
    assert key_path.exists()
    assert len(key_path.read_bytes()) >= 32


def test_load_uses_legacy_key_when_user_key_missing(tmp_path):
    base_dir = tmp_path / "masterData"
    user_dir = base_dir / "users" / "abc" / "data"
    user_dir.mkdir(parents=True)

    CsvStore(str(base_dir))
    key_bytes = (base_dir / ".demandas.key").read_bytes()

    store = CsvStore(str(user_dir))
    store._crypto_key = key_bytes[:32]
    store.add(_payload())

    (user_dir / ".demandas.key").unlink()

    reopened = CsvStore(str(user_dir))
    rows = reopened.build_view()
    assert len(rows) == 1
    assert rows[0]["Projeto"] == "Projeto Secreto"
    assert (user_dir / ".demandas.key").read_bytes()[:32] == key_bytes[:32]


def test_uses_legacy_data2_csv_as_primary_when_data_csv_missing(tmp_path):
    store = CsvStore(str(tmp_path))
    store.add(_payload())

    data_csv = tmp_path / "data.csv"
    legacy_csv = tmp_path / "data2.csv"
    data_csv.replace(legacy_csv)

    reopened = CsvStore(str(tmp_path))
    rows = reopened.build_view()
    assert len(rows) == 1
    assert rows[0]["Projeto"] == "Projeto Secreto"
    assert reopened.csv_path.endswith("data2.csv")
