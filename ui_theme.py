from __future__ import annotations

from typing import Tuple

from PySide6.QtCore import QFile, QTextStream

import mydemands.resources_rc  # noqa: F401


def _read_qss(resource_path: str) -> str:
    file = QFile(resource_path)
    if not file.open(QFile.ReadOnly | QFile.Text):
        raise RuntimeError(f"Erro ao carregar QSS: {resource_path}")
    stream = QTextStream(file)
    content = stream.readAll().strip()
    file.close()
    return content


def build_app_stylesheet(theme: str = "light") -> str:
    normalized = (theme or "light").strip().lower()
    color_resource = ":/styles/dark_colors.qss" if normalized == "dark" else ":/styles/light_colors.qss"
    return f"{_read_qss(':/styles/base.qss')}\n\n{_read_qss(color_resource)}\n"


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
