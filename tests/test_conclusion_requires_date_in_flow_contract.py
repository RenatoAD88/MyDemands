from csv_store import CsvStore

def test_concluded_record_has_date_and_percent_1(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add({
        "Descrição": "X",
        "Projeto": "Projeto X",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Concluído",
        "Data Conclusão": "06/02/2026",
        "Responsável": "R",
        "% Conclusão": "1",
    })
    dr = store.get(_id)
    assert dr is not None
    assert dr.data["Status"] == "Concluído"
    assert dr.data["Data Conclusão"] == "06/02/2026"
    assert dr.data["% Conclusão"] in ("1", "1.0")
