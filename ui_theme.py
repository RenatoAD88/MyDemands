from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple


def _runtime_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def _styles_dir() -> Path:
    return _runtime_root() / "mydemands" / "ui" / "styles"


def _read_qss(filename: str) -> str:
    path = _styles_dir() / filename
    if not path.exists():
        raise RuntimeError(f"QSS não encontrado: {path}")
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
