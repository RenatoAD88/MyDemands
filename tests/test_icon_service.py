import pytest

qtgui = pytest.importorskip("PySide6.QtGui", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from mydemands.services.icon_service import IconService

QSize = qtcore.QSize
QIcon = qtgui.QIcon


def test_get_icon_export_by_theme_returns_valid_icons():
    service = IconService()

    dark_icon = service.get_icon("export", "dark")
    light_icon = service.get_icon("export", "light")

    assert isinstance(dark_icon, QIcon)
    assert isinstance(light_icon, QIcon)
    assert dark_icon.isNull() is False
    assert light_icon.isNull() is False


def test_icon_size_is_consistent_across_themes():
    service = IconService()

    assert service.icon_size("light") == QSize(24, 24)
    assert service.icon_size("dark") == QSize(24, 24)


def test_import_export_icon_paths_follow_semantic_direction():
    service = IconService()

    assert service._ICON_FILES["export"]["light"].endswith("export_light.svg")
    assert service._ICON_FILES["export"]["dark"].endswith("export_dark.svg")
    assert service._ICON_FILES["import"]["light"].endswith("import_light.svg")
    assert service._ICON_FILES["import"]["dark"].endswith("import_dark.svg")
