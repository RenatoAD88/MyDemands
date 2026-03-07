from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class DemandFieldMapEntry:
    ui_label: str
    internal_name: str
    csv_column: str


FIELD_MAP = (
    DemandFieldMapEntry("Data de Registro", "data_registro", "Data de Registro"),
    DemandFieldMapEntry("Data Conclusão", "data_conclusao", "Data Conclusão"),
    DemandFieldMapEntry("Prazo", "prazo", "Prazo"),
    DemandFieldMapEntry("Status", "status", "Status"),
    DemandFieldMapEntry("Prioridade", "prioridade", "Prioridade"),
    DemandFieldMapEntry("É Urgente?", "urgente", "É Urgente?"),
    DemandFieldMapEntry("Reportar?", "reportar", "Reportar?"),
    DemandFieldMapEntry("Descrição", "descricao", "Descrição"),
    DemandFieldMapEntry("Comentário", "comentario", "Comentário"),
    DemandFieldMapEntry("Projeto", "projeto", "Projeto"),
    DemandFieldMapEntry("Responsável", "responsavel", "Responsável"),
    DemandFieldMapEntry("% Conclusão", "percentual_conclusao", "% Conclusão"),
)


_ALIAS_TO_CSV: Dict[str, str] = {}
for entry in FIELD_MAP:
    aliases = {
        entry.ui_label,
        entry.csv_column,
        entry.internal_name,
        entry.ui_label.casefold(),
        entry.csv_column.casefold(),
        entry.internal_name.casefold(),
        entry.internal_name.replace("_", " "),
        entry.internal_name.replace("_", " ").casefold(),
    }
    for alias in aliases:
        _ALIAS_TO_CSV[str(alias).strip()] = entry.csv_column


def resolve_csv_field_name(field_name: str) -> Optional[str]:
    key = str(field_name or "").strip()
    if not key:
        return None
    return _ALIAS_TO_CSV.get(key) or _ALIAS_TO_CSV.get(key.casefold())

