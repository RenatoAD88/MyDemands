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
