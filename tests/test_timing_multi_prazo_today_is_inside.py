from datetime import date
import csv_store


def test_timing_multi_prazo_if_contains_today_is_dentro_do_prazo():
    today = date(2026, 2, 6)

    # prazos contém ontem e hoje -> deve ser Dentro do Prazo
    prazos = [date(2026, 2, 5), date(2026, 2, 6)]
    t = csv_store.calc_timing("Não iniciada", prazos, conclusao=None, today=today)
    assert t == "Dentro do Prazo"
