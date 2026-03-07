from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List

from PySide6.QtCore import QObject, QTimer

LOGGER = logging.getLogger(__name__)


class TransientPersistenceError(Exception):
    """Erro técnico transitório no processo de persistência."""


@dataclass
class DateFieldSaveJob:
    demand_id: str
    field_name: str
    old_value: str
    new_value: str
    changed_at: datetime
    attempts: int = 0


@dataclass
class DateFieldSaveResult:
    ok: bool
    demand_id: str
    field_name: str
    old_value: str
    new_value: str
    attempt: int
    max_attempts: int
    error: str = ""


class DateFieldPersistenceService(QObject):
    def __init__(
        self,
        persist_callable: Callable[[str, str, str], None],
        on_result: Callable[[DateFieldSaveResult], None],
        *,
        max_attempts: int = 3,
        retry_delay_ms: int = 150,
    ) -> None:
        super().__init__()
        self._persist_callable = persist_callable
        self._on_result = on_result
        self._max_attempts = max(1, int(max_attempts or 1))
        self._retry_delay_ms = max(1, int(retry_delay_ms or 1))
        self._queue: List[DateFieldSaveJob] = []
        self._running = False

    def enqueue(self, job: DateFieldSaveJob) -> None:
        self._queue.append(job)
        LOGGER.info(
            "Date save enqueued demand_id=%s field=%s old=%r new=%r queued=%s",
            job.demand_id,
            job.field_name,
            job.old_value,
            job.new_value,
            len(self._queue),
        )
        if not self._running:
            self._running = True
            QTimer.singleShot(0, self._process_next)

    def has_pending(self) -> bool:
        return self._running or bool(self._queue)

    def _process_next(self) -> None:
        if not self._queue:
            self._running = False
            return

        job = self._queue.pop(0)
        job.attempts += 1
        LOGGER.info(
            "Date save attempt demand_id=%s field=%s attempt=%s/%s changed_at=%s",
            job.demand_id,
            job.field_name,
            job.attempts,
            self._max_attempts,
            job.changed_at.isoformat(),
        )

        try:
            self._persist_callable(job.demand_id, job.field_name, job.new_value)
        except Exception as exc:
            LOGGER.exception(
                "Date save failure demand_id=%s field=%s attempt=%s/%s error=%s",
                job.demand_id,
                job.field_name,
                job.attempts,
                self._max_attempts,
                exc,
            )
            if self._is_transient_error(exc) and job.attempts < self._max_attempts:
                self._queue.insert(0, job)
                QTimer.singleShot(self._retry_delay_ms * job.attempts, self._process_next)
                return

            self._on_result(
                DateFieldSaveResult(
                    ok=False,
                    demand_id=job.demand_id,
                    field_name=job.field_name,
                    old_value=job.old_value,
                    new_value=job.new_value,
                    attempt=job.attempts,
                    max_attempts=self._max_attempts,
                    error=str(exc),
                )
            )
            QTimer.singleShot(0, self._process_next)
            return

        self._on_result(
            DateFieldSaveResult(
                ok=True,
                demand_id=job.demand_id,
                field_name=job.field_name,
                old_value=job.old_value,
                new_value=job.new_value,
                attempt=job.attempts,
                max_attempts=self._max_attempts,
            )
        )
        QTimer.singleShot(0, self._process_next)

    @staticmethod
    def _is_transient_error(exc: Exception) -> bool:
        return isinstance(exc, (TransientPersistenceError, OSError, IOError, PermissionError, BlockingIOError))
