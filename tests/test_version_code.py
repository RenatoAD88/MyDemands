import pytest

pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import build_version_code


def test_build_version_code_uses_rad_with_previous_commit_format():
    assert build_version_code(7) == "RAD_2026_7"


def test_build_version_code_uses_first_version_when_git_is_unavailable(monkeypatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("git indisponível")

    monkeypatch.setattr("app.subprocess.check_output", _raise)
    assert build_version_code() == "RAD_2026_81"
