import csv

from csv_store import CsvStore


def test_export_all_to_csv_exports_existing_demands(tmp_path):
    store = CsvStore(str(tmp_path))

    first_id = store.add({
        "Descrição": "Demanda A",
        "Projeto": "Projeto Atlas",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "Ana",
    })
    second_id = store.add({
        "Descrição": "Demanda B",
        "Projeto": "Projeto Boreal",
        "Prioridade": "Baixa",
        "Prazo": "10/02/2026",
        "Data de Registro": "02/02/2026",
        "Status": "Em espera",
        "Responsável": "Bruno",
    })

    export_path = tmp_path / "export.csv"
    total = store.export_all_to_csv(str(export_path))

    assert total == 2
    assert export_path.exists()

    with export_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=","))

    assert len(rows) == 2
    exported_ids = [row["ID"] for row in rows]
    assert exported_ids == ["1", "2"]

    exported_projects = [row["Projeto"] for row in rows]
    assert exported_projects == ["Projeto Atlas", "Projeto Boreal"]

    assert first_id != second_id


def test_export_all_to_csv_flattens_multiline_prazo(tmp_path):
    store = CsvStore(str(tmp_path))
    store.add({
        "Descrição": "Demanda C",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026, 06/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "Ana",
    })

    export_path = tmp_path / "export.csv"
    store.export_all_to_csv(str(export_path))

    with export_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=","))

    assert rows[0]["Prazo"] == "05/02/2026,06/02/2026"


def test_export_all_to_csv_writes_utf8_bom_for_excel_compatibility(tmp_path):
    store = CsvStore(str(tmp_path))
    store.add({
        "Descrição": "Ação com acentuação",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "José",
    })

    export_path = tmp_path / "export.csv"
    store.export_all_to_csv(str(export_path))

    raw = export_path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")

    with export_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=","))

    assert rows[0]["Descrição"] == "Ação com acentuação"
