from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from csv_store import CSV_COLUMNS
from validation import ValidationError
from mydemands.dashboard.demand_field_map import resolve_csv_field_name


LOGGER = logging.getLogger(__name__)


class DemandUpdateService:
    def __init__(
        self,
        update_callable: Callable[[str, Dict[str, Any]], None],
        get_callable: Callable[[str], Any],
        after_update: Callable[[], None] | None = None,
        lookup_state_callable: Callable[[str], Dict[str, Any]] | None = None,
        on_missing_record: Callable[[str, str | None], None] | None = None,
    ):
        self._update_callable = update_callable
        self._get_callable = get_callable
        self._after_update = after_update
        self._lookup_state_callable = lookup_state_callable
        self._on_missing_record = on_missing_record

    def update(self, demand_id: str, changes: Dict[str, Any], source_context: str | None = None) -> Dict[str, Any]:
        return self.update_demand_field(demand_id=demand_id, changes=changes, source_context=source_context)

    def update_demand_field(self, demand_id: str, changes: Dict[str, Any], source_context: str | None = None) -> Dict[str, Any]:
        demand_id = str(demand_id or "").strip()
        if not demand_id:
            raise ValidationError("ID da demanda não informado.")

        existing = self._get_callable(demand_id)
        if existing is None:
            lookup_state = {}
            if self._lookup_state_callable:
                try:
                    lookup_state = self._lookup_state_callable(demand_id) or {}
                except Exception:
                    LOGGER.exception("Falha ao coletar estado de lookup demand_id=%s", demand_id)
            LOGGER.error(
                "Demand update failed: missing demand_id=%s source=%s lookup_state=%s",
                demand_id,
                source_context or "unspecified",
                lookup_state,
            )
            if self._on_missing_record:
                try:
                    self._on_missing_record(demand_id, source_context)
                except Exception:
                    LOGGER.exception("Falha ao processar recarga segura para demand_id=%s", demand_id)
            raise ValidationError("Não foi possível localizar a demanda selecionada. A lista será recarregada.")

        normalized_changes: Dict[str, Any] = {}
        for field_name, value in (changes or {}).items():
            resolved = resolve_csv_field_name(str(field_name or ""))
            if not resolved or resolved not in CSV_COLUMNS:
                raise ValidationError(f"Campo não suportado para atualização: {field_name}.")
            normalized_changes[resolved] = value

        if not normalized_changes:
            raise ValidationError("Nenhum campo válido foi informado para atualização.")

        before = {k: existing.data.get(k) for k in normalized_changes.keys()}
        LOGGER.debug(
            "Demand update request demand_id=%s source=%s changes=%s before=%s",
            demand_id,
            source_context or "unspecified",
            normalized_changes,
            before,
        )

        self._update_callable(demand_id, normalized_changes)

        if self._after_update:
            try:
                self._after_update()
            except Exception:
                LOGGER.exception("Falha em pós-atualização da demanda demand_id=%s", demand_id)

        updated = self._get_callable(demand_id)
        after = {k: (updated.data.get(k) if updated else None) for k in normalized_changes.keys()}
        result = {
            "ok": True,
            "demand_id": demand_id,
            "source_context": source_context or "unspecified",
            "applied_changes": normalized_changes,
            "before": before,
            "after": after,
        }
        LOGGER.debug("Demand update success demand_id=%s result=%s", demand_id, result)
        return result
