import pytest

pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import build_version_code


def test_build_version_code_uses_rad_with_previous_commit_format():
    assert build_version_code("d1cdab8") == "RAD_d1cdab8"
