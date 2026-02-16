from pathlib import Path

from ai_writing import error_log
from ai_writing.errors import MissingAPIKeyError, RateLimitError


def test_log_ai_generation_error_maps_missing_key_message(tmp_path, monkeypatch):
    monkeypatch.setattr(error_log, "resolve_storage_root", lambda: str(tmp_path))

    log_path = error_log.log_ai_generation_error(
        MissingAPIKeyError("token ausente"),
        context={"field": "Descrição"},
    )

    content = Path(log_path).read_text(encoding="utf-8")
    assert "missing_key" in content
    assert "token ausente" not in content


def test_log_ai_generation_error_preserves_known_error_messages(tmp_path, monkeypatch):
    monkeypatch.setattr(error_log, "resolve_storage_root", lambda: str(tmp_path))

    log_path = error_log.log_ai_generation_error(
        RateLimitError("429"),
        context={"field": "Descrição"},
    )

    content = Path(log_path).read_text(encoding="utf-8")
    assert "429" in content
