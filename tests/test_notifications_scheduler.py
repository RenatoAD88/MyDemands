import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dataclasses import dataclass
from datetime import datetime

from notifications.models import NotificationType
from notifications.scheduler import DeadlineScheduler


@dataclass
class FixedTimeProvider:
    current: datetime

    def now(self) -> datetime:
        return self.current


class Repo:
    def list_open_demands(self):
        return [
            {"ID": "123", "Prazo": "11/01/2026"},
            {"ID": "222", "Prazo": "10/01/2026"},
            {"ID": "333", "Prazo": "09/01/2026"},
            {"ID": "444", "Prazo": ""},
        ]


def test_scheduler_generates_proximo_and_estourado_events():
    captured = []

    scheduler = DeadlineScheduler(
        repo=Repo(),
        emitter=lambda n: captured.append(n),
        time_provider=FixedTimeProvider(datetime(2026, 1, 10, 8, 0, 0)),
    )

    events = scheduler.check_now()

    event_types = [evt.notification_type for evt in events]
    assert NotificationType.PRAZO_PROXIMO in event_types
    assert NotificationType.PRAZO_ESTOURADO in event_types

    assert any(n.payload.get("demand_id") == "123" and n.type == NotificationType.PRAZO_PROXIMO for n in captured)
    assert any(n.payload.get("demand_id") == "333" and n.type == NotificationType.PRAZO_ESTOURADO for n in captured)
