from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, List

from csv_store import parse_prazos_list

PENDING_ACTIVE_STATUSES = {"não iniciada", "em andamento", "bloqueado", "requer revisão", "requer revisao"}


@dataclass(frozen=True)
class EisenhowerQuadrant:
    key: str
    title: str


QUADRANTS: List[EisenhowerQuadrant] = [
    EisenhowerQuadrant("q1", "Importante e Urgente"),
    EisenhowerQuadrant("q2", "Não importante e Urgente"),
    EisenhowerQuadrant("q3", "Importante e Não urgente"),
    EisenhowerQuadrant("q4", "Não importante e Não urgente"),
]


class EisenhowerClassifierService:
    def __init__(self, today_provider: Callable[[], date] | None = None):
        self._today_provider = today_provider or date.today

    def should_include(self, row: Dict[str, Any]) -> bool:
        status = (row.get("Status") or "").strip().casefold()
        return status in PENDING_ACTIVE_STATUSES

    def classify(self, row: Dict[str, Any]) -> str:
        if not self.should_include(row):
            return "excluded"

        important = self._is_important(row)
        urgent = self._is_urgent(row)
        if important and urgent:
            return "q1"
        if (not important) and urgent:
            return "q2"
        if important and (not urgent):
            return "q3"
        return "q4"

    def group_rows(self, rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        groups = {q.key: [] for q in QUADRANTS}
        for row in rows:
            key = self.classify(row)
            if key in groups:
                groups[key].append(row)
        return groups

    def _is_important(self, row: Dict[str, Any]) -> bool:
        priority = (row.get("Prioridade") or "Média").strip().casefold()
        if priority not in {"alta", "média", "media", "baixa"}:
            priority = "média"
        return priority in {"alta", "média", "media"}

    def _is_urgent(self, row: Dict[str, Any]) -> bool:
        is_urgent = (row.get("É Urgente?") or "Não").strip().casefold() == "sim"
        timing = (row.get("Timing") or "").strip().casefold()
        delayed = "atras" in timing
        return is_urgent or delayed or self._is_due_today(row)

    def _is_due_today(self, row: Dict[str, Any]) -> bool:
        today = self._today_provider()
        raw_deadline = str(row.get("Prazo") or "")
        normalized = raw_deadline.replace("*", "").replace("\n", ",")
        return today in parse_prazos_list(normalized)
