import csv

import pytest

from csv_store import CsvStore, DISPLAY_COLUMNS
from validation import ValidationError


def _sample_payload(status: str = "Não iniciada", percent: str = "0"):
    return {
        "É Urgente?": "Não",
        "Status": status,
        "Prioridade": "Média",
        "Data de Registro": "01/01/2025",
        "Prazo": "10/01/2025, 11/01/2025",
        "Data Conclusão": "",
        "Projeto": "Projeto Import",
        "Descrição": "Descrição importada",
        "ID Azure": "AZ-1",
        "% Conclusão": percent,
        "Responsável": "Time X",
        "Reportar?": "Não",
        "Nome": "Nome X",
        "Time/Função": "Dev",
    }


def test_import_from_exported_csv_replaces_existing_rows(tmp_path):
    store = CsvStore(str(tmp_path))
    store.add(_sample_payload())

    export_path = tmp_path / "export.csv"
    with export_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DISPLAY_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "ID": "1",
                "É Urgente?": "Sim",
                "Status": "Em andamento",
                "Timing": "Dentro do Prazo",
                "Prioridade": "Alta",
                "Data de Registro": "02/01/2025",
                "Prazo": "15/01/2025,16/01/2025",
                "Data Conclusão": "",
                "Projeto": "Projeto Novo",
                "Descrição": "Nova demanda",
                "ID Azure": "AZ-2",
                "% Conclusão": "50%",
                "Responsável": "Pessoa A",
                "Reportar?": "Sim",
                "Nome": "Nome A",
                "Time/Função": "QA",
            }
        )

    imported = store.import_from_exported_csv(str(export_path))

    assert imported == 1
    rows = store.build_view()
    assert len(rows) == 1
    assert rows[0]["Projeto"] == "Projeto Novo"
    assert rows[0]["% Conclusão"] == "50%"


def test_import_from_exported_csv_rejects_invalid_header(tmp_path):
    store = CsvStore(str(tmp_path))
    import_path = tmp_path / "invalid_header.csv"

    with import_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["coluna", "invalida"])
        writer.writerow(["x", "y"])

    with pytest.raises(ValidationError, match="Formato de CSV inválido"):
        store.import_from_exported_csv(str(import_path))


def test_import_from_exported_csv_rejects_invalid_row_and_keeps_existing_data(tmp_path):
    store = CsvStore(str(tmp_path))
    store.add(_sample_payload())
    original_project = store.build_view()[0]["Projeto"]

    import_path = tmp_path / "invalid_row.csv"
    with import_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=DISPLAY_COLUMNS)
        writer.writeheader()
        row = {
            "ID": "1",
            "É Urgente?": "Não",
            "Status": "Concluído",
            "Timing": "Concluído",
            "Prioridade": "Média",
            "Data de Registro": "01/01/2025",
            "Prazo": "10/01/2025",
            "Data Conclusão": "",
            "Projeto": "Projeto inválido",
            "Descrição": "Sem data de conclusão",
            "ID Azure": "AZ-3",
            "% Conclusão": "100%",
            "Responsável": "Time",
            "Reportar?": "Não",
            "Nome": "Nome",
            "Time/Função": "Dev",
        }
        writer.writerow(row)

    with pytest.raises(ValidationError, match=r"Erro na linha 2"):
        store.import_from_exported_csv(str(import_path))

    rows = store.build_view()
    assert len(rows) == 1
    assert rows[0]["Projeto"] == original_project
