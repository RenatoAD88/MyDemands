from datetime import date
import csv_store

def test_timing_multi_prazo_contains_today_is_dentro_do_prazo():
    today = date(2026, 2, 6)
    prazos = [date(2026, 2, 5), date(2026, 2, 6)]
    t = csv_store.calc_timing("Em andamento", prazos, conclusao=None, today=today)
    assert t == "Dentro do Prazo"
