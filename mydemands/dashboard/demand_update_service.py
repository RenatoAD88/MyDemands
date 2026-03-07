from __future__ import annotations

import logging
from typing import Any, Callable, Dict


LOGGER = logging.getLogger(__name__)


class DemandUpdateService:
    def __init__(self, update_callable: Callable[[str, Dict[str, Any]], None], after_update: Callable[[], None] | None = None):
        self._update_callable = update_callable
        self._after_update = after_update

    def update(self, demand_id: str, changes: Dict[str, Any]) -> None:
        self._update_callable(demand_id, changes)
        if self._after_update:
            try:
                self._after_update()
            except Exception:
                LOGGER.exception("Falha em pós-atualização da demanda demand_id=%s", demand_id)
