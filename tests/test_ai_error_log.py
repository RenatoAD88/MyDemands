from pathlib import Path

from ai_writing import error_log


def test_ai_log_dir_uses_storage_root_and_creates_log_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(error_log, "resolve_storage_root", lambda: str(tmp_path))

    log_dir = error_log.ai_log_dir()

    assert log_dir == str(tmp_path / "log")
    assert (tmp_path / "log").is_dir()


def test_append_ai_error_log_writes_message_context_and_trace(tmp_path, monkeypatch):
    monkeypatch.setattr(error_log, "resolve_storage_root", lambda: str(tmp_path))

    log_path = error_log.append_ai_error_log(
        "Falha de teste",
        traceback_text="Traceback test line",
        context={"demand_id": "123", "field": "Descrição"},
    )

    content = Path(log_path).read_text(encoding="utf-8")
    assert "Falha de teste" in content
    assert "demand_id" in content
    assert "Traceback test line" in content


def test_append_ai_error_log_uses_openia_error_filename(tmp_path, monkeypatch):
    monkeypatch.setattr(error_log, "resolve_storage_root", lambda: str(tmp_path))

    log_path = error_log.append_ai_error_log("Falha")

    assert Path(log_path).name == "openIA_error.log"
