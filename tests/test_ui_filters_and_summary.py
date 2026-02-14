from ui_filters import filter_rows, summary_counts


def test_filter_rows_applies_text_and_status():
    rows = [
        {"Projeto": "ERP", "Descrição": "Migrar", "Responsável": "Ana", "Status": "Em andamento", "Prioridade": "Alta"},
        {"Projeto": "CRM", "Descrição": "Ajuste", "Responsável": "Bruno", "Status": "Em espera", "Prioridade": "Baixa"},
    ]
    out = filter_rows(rows, text_query="erp", status="Em andamento")
    assert len(out) == 1
    assert out[0]["Projeto"] == "ERP"


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


def test_filter_rows_applies_comentario_filter():
    rows = [
        {"Projeto": "ERP", "Descrição": "Migrar", "Responsável": "Ana", "Status": "Em andamento", "Prioridade": "Alta", "Comentário": "Aguardando retorno"},
        {"Projeto": "CRM", "Descrição": "Ajuste", "Responsável": "Bruno", "Status": "Em espera", "Prioridade": "Baixa", "Comentário": "Finalizado"},
    ]
    out = filter_rows(rows, comentario="retorno")
    assert len(out) == 1
    assert out[0]["Projeto"] == "ERP"
