from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Tuple

EXPECTED_QSS_FILES = ("base.qss", "light_colors.qss", "dark_colors.qss")


def _runtime_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def _styles_dir() -> Path:
    return _runtime_root() / "mydemands" / "ui" / "styles"


def validate_packaged_qss(debug: bool = False) -> list[str]:
    styles_dir = _styles_dir()
    missing = [name for name in EXPECTED_QSS_FILES if not (styles_dir / name).exists()]
    if debug:
        present = sorted(p.name for p in styles_dir.glob("*.qss")) if styles_dir.exists() else []
        print(f"[QSS-CHECK] styles_dir={styles_dir}")
        print(f"[QSS-CHECK] arquivos presentes={present}")
        if missing:
            print(f"[QSS-CHECK] arquivos ausentes={missing}")
    return missing


def qss_self_test(verbose: bool = True) -> int:
    styles_dir = _styles_dir()
    missing = validate_packaged_qss(debug=False)
    if missing:
        if verbose:
            print(f"[QSS-SELF-TEST] FALHA: arquivos ausentes={missing}")
            print(f"[QSS-SELF-TEST] runtime_root={_runtime_root()}")
            print(f"[QSS-SELF-TEST] styles_dir={styles_dir}")
            ui_dir = _runtime_root() / "mydemands" / "ui"
            if ui_dir.exists() and ui_dir.is_dir():
                entries = sorted(p.name for p in ui_dir.iterdir())
                print(f"[QSS-SELF-TEST] mydemands/ui conteúdo={entries}")
            else:
                print(f"[QSS-SELF-TEST] diretório ausente: {ui_dir}")
        return 1

    if verbose:
        print(f"[QSS-SELF-TEST] OK: arquivos presentes em {styles_dir}")
    return 0


def _read_qss(filename: str) -> str:
    path = _styles_dir() / filename
    if not path.exists():
        if os.environ.get("MYDEMANDS_DEBUG_QSS", "").strip().lower() in {"1", "true", "yes"}:
            validate_packaged_qss(debug=True)
        details = [f"Build sem QSS. QSS não encontrado: {path}"]
        details.append(f"runtime_root={_runtime_root()}")
        ui_dir = _runtime_root() / "mydemands" / "ui"
        if ui_dir.exists() and ui_dir.is_dir():
            entries = sorted(p.name for p in ui_dir.iterdir())
            details.append(f"mydemands/ui conteúdo={entries}")
        else:
            details.append(f"diretório ausente: {ui_dir}")
        raise RuntimeError(" | ".join(details))
    return path.read_text(encoding="utf-8").strip()


def build_app_stylesheet(theme: str = "light") -> str:
    normalized = (theme or "light").strip().lower()
    base = _read_qss("base.qss")
    colors = _read_qss("dark_colors.qss" if normalized == "dark" else "light_colors.qss")
    return base + "\n" + colors


def status_color(status: str) -> Tuple[int, int, int]:
    s = (status or "").strip().lower()
    if s == "concluído" or s == "concluido":
        return (210, 242, 220)
    if s == "não iniciada" or s == "nao iniciada" or s == "não iniciado" or s == "nao iniciado":
        return (255, 228, 230)
    if s == "requer revisão" or s == "requer revisao":
        return (237, 233, 254)
    if s == "em espera":
        return (255, 243, 205)
    if s == "cancelado":
        return (238, 238, 238)
    return (230, 239, 255)


def timing_color(timing: str) -> Tuple[int, int, int]:
    t = (timing or "").strip().lower()
    if "atras" in t:
        return (255, 228, 230)
    if "sem prazo" in t:
        return (243, 244, 246)
    if "dentro" in t or "no prazo" in t:
        return (220, 252, 231)
    if "conclu" in t:
        return (224, 231, 255)
    return (243, 244, 246)
