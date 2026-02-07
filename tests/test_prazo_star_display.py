from datetime import date
from csv_store import CsvStore


def test_prazo_multi_dates_has_star_in_display(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add({
        "Descrição": "Multi prazo",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026, 06/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Não iniciada",
        "Responsável": "R",
    })

    row = next(x for x in store.build_view() if x["_id"] == _id)
    assert row["Prazo"] == "05/02/2026*, 06/02/2026*"

    # aparece em ambas as datas no filtro
    rows_0502 = store.tab1_by_prazo_date(date(2026, 2, 5))
    rows_0602 = store.tab1_by_prazo_date(date(2026, 2, 6))
    assert any(x["_id"] == _id for x in rows_0502)
    assert any(x["_id"] == _id for x in rows_0602)


def test_prazo_single_date_has_no_star(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add({
        "Descrição": "Single prazo",
        "Prioridade": "Baixa",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Não iniciada",
        "Responsável": "R",
    })

    row = next(x for x in store.build_view() if x["_id"] == _id)
    assert row["Prazo"] == "05/02/2026"
