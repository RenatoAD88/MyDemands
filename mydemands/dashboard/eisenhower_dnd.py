from __future__ import annotations

from typing import Any, Callable, Dict


class EisenhowerDnDController:
    QUADRANT_TO_FIELDS = {
        "q1": {"É Urgente?": "Sim", "Prioridade": "Alta"},
        "q2": {"É Urgente?": "Sim", "Prioridade": "Baixa"},
        "q3": {"É Urgente?": "Não", "Prioridade": "Média"},
        "q4": {"É Urgente?": "Não", "Prioridade": "Baixa"},
    }

    def __init__(self, move_executor: Callable[[Dict[str, Any], Dict[str, str]], None] | None):
        self._move_executor = move_executor

    def build_payload_for_target(self, target_quadrant: str) -> Dict[str, str]:
        return dict(self.QUADRANT_TO_FIELDS.get(target_quadrant, {}))

    def handle_move(self, source_quadrant: str, target_quadrant: str, row: Dict[str, Any]) -> None:
        if source_quadrant == target_quadrant or not self._move_executor:
            return
        payload = self.build_payload_for_target(target_quadrant)
        if not payload:
            return
        self._move_executor(row, payload)
