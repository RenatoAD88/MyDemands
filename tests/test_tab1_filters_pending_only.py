from datetime import date
from csv_store import CsvStore

def test_tab1_filters_out_cancelado_and_concluido_and_concluded_like(tmp_path):
    store = CsvStore(str(tmp_path))

    # pending
    a = store.add({
        "Descrição": "P",
        "Projeto": "Projeto P",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "R",
        "% Conclusão": "0.25",
    })

    # cancelado
    store.add({
        "Descrição": "C",
        "Projeto": "Projeto C",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Cancelado",
        "Responsável": "R",
        "% Conclusão": "0",
    })

    # concluído via status
    store.add({
        "Descrição": "D",
        "Projeto": "Projeto D",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Concluído",
        "Data Conclusão": "05/02/2026",
        "Responsável": "R",
        "% Conclusão": "1",
    })

    # concluído-like: status não concluído, mas % 100 + data conclusão
    store.add({
        "Descrição": "E",
        "Projeto": "Projeto E",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Data Conclusão": "05/02/2026",
        "Responsável": "R",
        "% Conclusão": "1",
    })

    rows = store.tab1_by_prazo_date(date(2026, 2, 5))
    ids = {r["_id"] for r in rows}
    assert a in ids
    assert len(ids) == 1
