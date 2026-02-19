from __future__ import annotations

from pathlib import Path
from typing import Tuple

_STYLE_DIR = Path(__file__).resolve().parent / "mydemands" / "ui" / "styles"


def _read_qss(filename: str) -> str:
    return (_STYLE_DIR / filename).read_text(encoding="utf-8").strip()


def build_app_stylesheet(theme: str = "light") -> str:
    normalized = (theme or "light").strip().lower()
    color_file = "dark_colors.qss" if normalized == "dark" else "light_colors.qss"
    return f"{_read_qss('base.qss')}\n\n{_read_qss(color_file)}\n"


APP_STYLESHEET = build_app_stylesheet("light")


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
