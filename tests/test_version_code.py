from datetime import datetime

import pytest

pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import build_version_code


def test_build_version_code_uses_rad_and_timestamp_pattern():
    ref = datetime(2026, 2, 21, 22, 24, 50)
    assert build_version_code(ref) == "RAD20260221222450"
