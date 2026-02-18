from __future__ import annotations

import os
from typing import Dict

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QStyle


class IconService:
    ICON_SIZE = QSize(24, 24)

    _ICON_FILES: Dict[str, Dict[str, str]] = {
        "new_demand": {"light": "new_demand_light.svg", "dark": "new_demand_dark.svg"},
        "delete": {"light": "delete_light.svg", "dark": "delete_dark.svg"},
        "export": {"light": "export_light.svg", "dark": "export_dark.svg"},
        "import": {"light": "import_light.svg", "dark": "import_dark.svg"},
    }

    _FALLBACKS = {
        "new_demand": QStyle.SP_FileDialogNewFolder,
        "delete": QStyle.SP_TrashIcon,
        "export": QStyle.SP_ArrowUp,
        "import": QStyle.SP_ArrowDown,
    }

    def __init__(self, base_dir: str | None = None):
        root = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._img_dir = os.path.join(root, "img")

    def icon_size(self, _theme: str) -> QSize:
        return QSize(self.ICON_SIZE)

    def get_icon(self, name: str, theme: str) -> QIcon:
        normalized_theme = "dark" if (theme or "").strip().lower() == "dark" else "light"
        by_theme = self._ICON_FILES.get(name, {})
        file_name = by_theme.get(normalized_theme) or by_theme.get("light")
        if file_name:
            icon_path = os.path.join(self._img_dir, file_name)
            if os.path.exists(icon_path):
                return QIcon(icon_path)
        return QIcon()

    def fallback_for(self, name: str) -> QStyle.StandardPixmap:
        return self._FALLBACKS.get(name, QStyle.SP_FileIcon)
