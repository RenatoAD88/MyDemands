from __future__ import annotations

import ast
from pathlib import Path

from mydemands.web import SCREEN_REGISTRY


ROOT = Path(__file__).resolve().parents[2]


def _qt_screen_classes(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"))
    classes: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            base_name = getattr(base, "id", None) or getattr(base, "attr", None)
            if base_name in {"QDialog", "QMainWindow"}:
                if node.name.startswith("Base"):
                    continue
                classes.add(node.name)
    return classes


def test_all_dialog_and_mainwindow_screens_are_mapped_to_web() -> None:
    desktop_screens = set()
    desktop_screens |= _qt_screen_classes(ROOT / "app.py")
    desktop_screens |= _qt_screen_classes(ROOT / "mydemands/ui/login_window.py")

    dialogs_dir = ROOT / "mydemands/ui/dialogs"
    for file in dialogs_dir.glob("*.py"):
        desktop_screens |= _qt_screen_classes(file)

    dashboard_file = ROOT / "mydemands/dashboard/grid_widgets.py"
    desktop_screens |= _qt_screen_classes(dashboard_file)

    mapped = {
        screen.source.rsplit(".", 1)[-1]
        for screen in SCREEN_REGISTRY
        if "." in screen.source and "tab" not in screen.source
    }

    missing = desktop_screens - mapped
    assert not missing, f"Telas desktop sem rota web: {sorted(missing)}"


def test_all_main_tabs_have_web_routes() -> None:
    source = (ROOT / "app.py").read_text(encoding="utf-8")
    tab_titles = {
        "Presenças do Time",
        "Consultar Demandas Pendentes",
        "Consultar Demandas Concluídas",
        "Monitoramento",
    }
    # sanity check: prevent stale expectations
    for title in tab_titles:
        assert title in source

    mapped_tabs = {screen.title for screen in SCREEN_REGISTRY if screen.kind == "tab"}
    assert tab_titles.issubset(mapped_tabs)
