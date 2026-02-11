from ui_filters import filter_rows, summary_counts


def test_filter_rows_applies_text_and_status():
    rows = [
        {"Projeto": "ERP", "Descrição": "Migrar", "Responsável": "Ana", "Status": "Em andamento", "Prioridade": "Alta"},
        {"Projeto": "CRM", "Descrição": "Ajuste", "Responsável": "Bruno", "Status": "Em espera", "Prioridade": "Baixa"},
    ]
    out = filter_rows(rows, text_query="erp", status="Em andamento")
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
    assert counts == {"pending": 2, "delayed": 1, "concluded": 1}
