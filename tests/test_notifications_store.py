import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime

from notifications.models import Notification, NotificationType
from notifications.store import NotificationStore


def test_store_insert_list_mark_read_and_filters(tmp_path):
    store = NotificationStore(str(tmp_path))
    id1 = store.insert(
        Notification(
            type=NotificationType.NOVA_DEMANDA,
            title="Nova demanda atribuída",
            body="Demanda #123 criada.",
            timestamp=datetime(2026, 1, 1, 10, 0, 0),
        )
    )
    id2 = store.insert(
        Notification(
            type=NotificationType.PRAZO_ESTOURADO,
            title="Demanda #999 atrasada",
            body="Prazo vencido.",
            timestamp=datetime(2026, 1, 1, 11, 0, 0),
        )
    )

    all_items = store.list_notifications(limit=10)
    assert [n.id for n in all_items] == [id2, id1]

    by_type = store.list_notifications(type_filter=NotificationType.NOVA_DEMANDA)
    assert len(by_type) == 1
    assert by_type[0].title == "Nova demanda atribuída"

    unread = store.list_notifications(read_filter=False)
    assert len(unread) == 2

    store.mark_as_read(id1)
    unread_after = store.list_notifications(read_filter=False)
    assert [n.id for n in unread_after] == [id2]

    read_items = store.list_notifications(read_filter=True)
    assert [n.id for n in read_items] == [id1]

    assert store.enc_csv_path.endswith("notifications_history.enc.csv")


def test_store_marks_occurrence_as_already_notified_after_read_or_delete(tmp_path):
    store = NotificationStore(str(tmp_path))
    notif = Notification(
        type=NotificationType.PRAZO_PROXIMO,
        title="Prazo hoje: #10",
        body="Demanda vence em 11/01/2026.",
        payload={"demand_id": "10", "deadline_date": "2026-01-11", "event_code": "deadline_due"},
        timestamp=datetime(2026, 1, 10, 8, 0, 0),
    )

    assert store.should_dispatch(notif) is True
    notif_id = store.insert(notif)
    assert store.should_dispatch(notif) is False

    store.mark_as_read(notif_id)
    assert store.should_dispatch(notif) is False

    store.delete_notification(notif_id)
    assert store.should_dispatch(notif) is False
