from csv_store import CsvStore


def test_concluded_cannot_be_deleted(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add({
        "Descrição": "Concluída",
        "Projeto": "Projeto Concluído",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Concluído",
        "Data Conclusão": "06/02/2026",
        "Responsável": "R",
        "% Conclusão": "1",
    })

    ok = store.delete_by_id(_id)
    assert ok is False

    store.load()
    assert store.get(_id) is not None
