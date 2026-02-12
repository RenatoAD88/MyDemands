import csv

from csv_store import CsvStore


def test_export_rows_to_csv_exports_only_selected_rows(tmp_path):
    store = CsvStore(str(tmp_path))

    id_1 = store.add({
        "Descrição": "Demanda 1",
        "Projeto": "Projeto 1",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "Ana",
    })
    store.add({
        "Descrição": "Demanda 2",
        "Projeto": "Projeto 2",
        "Prioridade": "Média",
        "Prazo": "06/02/2026",
        "Data de Registro": "02/02/2026",
        "Status": "Em espera",
        "Responsável": "Bia",
    })
    id_3 = store.add({
        "Descrição": "Demanda 3",
        "Projeto": "Projeto 3",
        "Prioridade": "Baixa",
        "Prazo": "07/02/2026",
        "Data de Registro": "03/02/2026",
        "Status": "Não iniciada",
        "Responsável": "Caio",
    })

    selected_ids = {id_1, id_3}
    selected_rows = [row for row in store.build_view() if row.get("_id") in selected_ids]

    export_path = tmp_path / "selected_export.csv"
    total = store.export_rows_to_csv(str(export_path), selected_rows)

    assert total == 2

    with export_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=","))

    assert [row["ID"] for row in rows] == ["1", "3"]
    assert [row["Projeto"] for row in rows] == ["Projeto 1", "Projeto 3"]
