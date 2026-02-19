from PySide6.QtCore import QCoreApplication

import mydemands.resources_rc  # noqa: F401
from ui_theme import _read_qss


def test_resources_accepts_legacy_double_colon_prefix():
    content = _read_qss("::/styles/light_colors.qss")
    assert isinstance(content, str)
    assert content.strip()



def test_resources_loaded():
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    content = _read_qss(":/styles/base.qss")
    assert isinstance(content, str)
    assert content.strip()
