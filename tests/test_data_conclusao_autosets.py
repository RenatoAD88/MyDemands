from csv_store import CsvStore


def test_setting_data_conclusao_nao_autoseta_status_nem_percent_no_rollback(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add({
        "Descrição": "A",
        "Projeto": "Projeto A",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "R",
        "% Conclusão": "0.25",
    })

    store.update(_id, {"Data Conclusão": "06/02/2026"})
    dr = store.get(_id)
    assert dr is not None
    assert dr.data["Status"] == "Em andamento"
    assert dr.data["% Conclusão"] == "0.25"
    assert dr.data["Data Conclusão"] == "06/02/2026"
