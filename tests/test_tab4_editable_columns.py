import pytest

pytest.importorskip("PySide6", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import TAB4_EDITABLE_COLUMNS


def test_tab4_allows_status_editing():
    assert "Status" in TAB4_EDITABLE_COLUMNS
