from csv_store import CsvStore


def test_status_concluido_nao_exige_data_conclusao_com_rollback(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add({
        "Descrição": "Y",
        "Projeto": "Projeto Y",
        "Prioridade": "Média",
        "Prazo": "05/02/2026",
        "Data Entrada": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "R",
        "% Conclusão": "0.25",
    })

    store.update(_id, {"Status": "Concluído"})
    dr = store.get(_id)
    assert dr is not None
    assert dr.data["Status"] == "Concluído"
    assert dr.data["Data Conclusão"] == ""


def test_percent_100_nao_exige_data_conclusao_com_rollback(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add({
        "Descrição": "Z",
        "Projeto": "Projeto Z",
        "Prioridade": "Baixa",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "R",
        "% Conclusão": "0.75",
    })

    store.update(_id, {"% Conclusão": "1"})
    dr = store.get(_id)
    assert dr is not None
    assert dr.data["% Conclusão"] == "1"
    assert dr.data["Data Conclusão"] == ""
