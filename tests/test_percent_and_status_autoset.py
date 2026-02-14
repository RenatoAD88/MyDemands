from csv_store import CsvStore
from validation import ValidationError


def test_percent_display_is_percent_strings(tmp_path):
    store = CsvStore(str(tmp_path))
    _id = store.add({
        "Descrição": "X",
        "Projeto": "Projeto X",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data Entrada": "01/02/2026",
        "Status": "Não iniciada",
        "Responsável": "R",
        "% Conclusão": "0.25",
    })

    row = next(x for x in store.build_view() if x["_id"] == _id)
    assert row["% Conclusão"] == "25%"


def test_status_concluido_requires_data_conclusao_and_autosets_percent(tmp_path):
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

    # sem data conclusão => deve falhar
    try:
        store.update(_id, {"Status": "Concluído"})
        assert False, "Deveria ter falhado por falta de Data Conclusão"
    except ValidationError:
        pass

    # com data conclusão => ok, e % vira 1 automaticamente
    store.update(_id, {"Status": "Concluído", "Data Conclusão": "06/02/2026"})
    dr = store.get(_id)
    assert dr is not None
    assert dr.data["Status"] == "Concluído"
    assert dr.data["% Conclusão"] == "1"
    assert dr.data["Data Conclusão"] == "06/02/2026"


def test_percent_100_requires_data_conclusao_and_autosets_status(tmp_path):
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

    # % 100 sem data => falha
    try:
        store.update(_id, {"% Conclusão": "1"})
        assert False, "Deveria ter falhado por falta de Data Conclusão"
    except ValidationError:
        pass

    # % 100 com data => ok e status vira concluído automaticamente
    store.update(_id, {"% Conclusão": "1", "Data Conclusão": "06/02/2026"})
    dr = store.get(_id)
    assert dr.data["Status"] == "Concluído"
    assert dr.data["% Conclusão"] == "1"
    assert dr.data["Data Conclusão"] == "06/02/2026"
