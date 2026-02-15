from ui_filters import filter_rows, summary_counts


def test_filter_rows_applies_text_and_status():
    rows = [
        {"Projeto": "ERP", "Descrição": "Migrar", "Responsável": "Ana", "Status": "Em andamento", "Prioridade": "Alta"},
        {"Projeto": "CRM", "Descrição": "Ajuste", "Responsável": "Bruno", "Status": "Em espera", "Prioridade": "Baixa"},
    ]
    out = filter_rows(rows, text_query="erp", status="Em andamento")
    assert len(out) == 1
    assert out[0]["Projeto"] == "ERP"


def test_filter_rows_accepts_multiple_statuses():
    rows = [
        {"Projeto": "ERP", "Status": "Em andamento"},
        {"Projeto": "CRM", "Status": "Em espera"},
        {"Projeto": "Portal", "Status": "Não iniciada"},
    ]
    out = filter_rows(rows, status_values=["Em espera", "Não iniciada"])
    assert [row["Projeto"] for row in out] == ["CRM", "Portal"]


def test_filter_rows_applies_prazo_and_projeto_filters():
    rows = [
        {"Projeto": "ERP", "Descrição": "Migrar", "Responsável": "Ana", "Status": "Em andamento", "Prioridade": "Alta", "Prazo": "05/02/2026"},
        {"Projeto": "CRM", "Descrição": "Ajuste", "Responsável": "Bruno", "Status": "Em espera", "Prioridade": "Baixa", "Prazo": "06/02/2026"},
    ]
    out = filter_rows(rows, prazo="05/02/2026", projeto="ERP")
    assert len(out) == 1
    assert out[0]["Projeto"] == "ERP"


def test_summary_counts_tracks_pending_delayed_concluded():
    rows = [
        {"Status": "Em andamento", "Timing": "Dentro do Prazo"},
        {"Status": "Em espera", "Timing": "Em Atraso"},
        {"Status": "Concluído", "Timing": "Concluída no Prazo"},
        {"Status": "Cancelado", "Timing": "Cancelado"},
    ]
    counts = summary_counts(rows)
    assert counts == {"pending": 2, "inside_deadline": 1, "delayed": 1, "concluded": 1}


def test_filter_rows_keyword_matches_extended_fields():
    rows = [
        {
            "Projeto": "ERP",
            "Descrição": "Migrar",
            "Comentário": "Aguardando retorno",
            "ID Azure": "AB#10",
            "Responsável": "Ana",
            "Nome": "Item 1",
            "Time/Função": "Dados",
            "Status": "Em andamento",
            "Prioridade": "Alta",
        },
        {
            "Projeto": "CRM",
            "Descrição": "Ajuste",
            "Comentário": "Finalizado",
            "ID Azure": "AB#20",
            "Responsável": "Bruno",
            "Nome": "Item 2",
            "Time/Função": "QA",
            "Status": "Em espera",
            "Prioridade": "Baixa",
        },
    ]
    assert filter_rows(rows, text_query="retorno")[0]["Projeto"] == "ERP"
    assert filter_rows(rows, text_query="AB#20")[0]["Projeto"] == "CRM"
    assert filter_rows(rows, text_query="qa")[0]["Projeto"] == "CRM"
