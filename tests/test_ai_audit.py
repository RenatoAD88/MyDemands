import sqlite3

from ai_writing.audit import AIAuditLogger


def test_audit_does_not_store_full_text_in_privacy_mode(tmp_path):
    logger = AIAuditLogger(str(tmp_path))
    logger.log_event(
        event_type="generate",
        demand_id="10",
        field_name="Descrição",
        text="texto sensível",
        success=True,
        privacy_mode=True,
        debug_mode=True,
    )

    with sqlite3.connect(logger.path) as conn:
        row = conn.execute("SELECT text_size, debug_text FROM ai_events").fetchone()

    assert row[0] == len("texto sensível")
    assert row[1] is None
