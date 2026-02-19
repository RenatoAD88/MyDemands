from __future__ import annotations

from typing import Tuple

from PySide6.QtCore import QDir, QFile, QIODevice, QTextStream

import mydemands.resources_rc  # noqa: F401


def _normalize_resource_path(resource_path: str) -> str:
    normalized = (resource_path or "").strip()
    if not normalized:
        return normalized
    while normalized.startswith("::"):
        normalized = normalized[1:]
    if normalized.startswith("/") and not normalized.startswith(":/"):
        normalized = f":{normalized}"
    return normalized


def _read_qss(resource_path: str) -> str:
    normalized_path = _normalize_resource_path(resource_path)
    file = QFile(normalized_path)
    if not file.exists():
        available = ", ".join(list_styles_resources()) or "<vazio>"
        raise RuntimeError(
            f"Resource não existe: {normalized_path}. "
            f"Resources em :/styles => [{available}]"
        )
    if not file.open(QIODevice.ReadOnly | QIODevice.Text):
        available = ", ".join(list_styles_resources()) or "<vazio>"
        raise RuntimeError(
            f"Falha ao abrir resource: {normalized_path}. "
            f"Resources em :/styles => [{available}]"
        )
    stream = QTextStream(file)
    if hasattr(QTextStream, "Encoding"):
        stream.setEncoding(QTextStream.Encoding.Utf8)
    content = stream.readAll()
    file.close()
    return content


def list_styles_resources() -> list[str]:
    directory = QDir(":/styles")
    return sorted(directory.entryList(QDir.Files | QDir.NoDotAndDotDot))


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
