from csv_store import CsvStore

def test_delete_by_line_removes_record(tmp_path):
    store = CsvStore(str(tmp_path))

    a = store.add({
        "Descrição": "A",
        "Projeto": "Projeto A",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "R",
    })
    b = store.add({
        "Descrição": "B",
        "Projeto": "Projeto B",
        "Prioridade": "Média",
        "Prazo": "06/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em espera",
        "Responsável": "R",
    })

    view = store.build_view()
    assert view[0]["_id"] == a
    assert view[1]["_id"] == b

    ok = store.delete_by_line(1)
    assert ok is True

    store.load()
    view2 = store.build_view()
    assert len(view2) == 1
    assert view2[0]["_id"] == b
    assert view2[0]["ID"] == "2"
