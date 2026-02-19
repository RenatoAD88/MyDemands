from __future__ import annotations

import importlib
import logging
import os
import pkgutil
from importlib import resources
from typing import Tuple


logger = logging.getLogger(__name__)


if os.getenv("MYDEMANDS_DEBUG_THEME") == "1":
    try:
        styles_pkg = importlib.import_module("mydemands.ui.styles")

        available_qss = [name for _, name, _ in pkgutil.iter_modules(styles_pkg.__path__)]
        logger.debug("Styles package loaded from %s (children=%s)", getattr(styles_pkg, "__file__", "<namespace>"), available_qss)
    except Exception:
        logger.exception("Failed to import styles package 'mydemands.ui.styles'")


def _read_qss(filename: str) -> str:
    data = resources.files("mydemands.ui.styles").joinpath(filename).read_bytes()
    return data.decode("utf-8").strip()


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
