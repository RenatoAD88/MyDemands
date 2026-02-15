import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from notifications.dispatcher import NotificationDispatcher
from notifications.models import Channel, Notification, NotificationType, Preferences


class FakeStore:
    def __init__(self):
        self.saved = []
        self.pref = Preferences()

    def load_preferences(self):
        return self.pref

    def insert(self, notification):
        self.saved.append(notification)
        return len(self.saved)


class Sink:
    def __init__(self):
        self.calls = []

    def notify(self, title, body):
        self.calls.append((title, body))


def test_dispatcher_focused_uses_inapp_channel():
    store = FakeStore()
    store.pref.enabled_channels[Channel.IN_APP] = True
    store.pref.enabled_channels[Channel.SYSTEM] = True
    system = Sink()
    inapp = Sink()

    dispatcher = NotificationDispatcher(
        store=store,
        system_notifier=system,
        inapp_notifier=inapp,
        is_app_focused=lambda: True,
    )

    dispatcher.dispatch(Notification(type=NotificationType.NOVA_DEMANDA, title="t", body="b"))
    assert len(inapp.calls) == 1
    assert len(system.calls) == 0


def test_dispatcher_background_uses_system_channel():
    store = FakeStore()
    store.pref.enabled_channels[Channel.IN_APP] = True
    store.pref.enabled_channels[Channel.SYSTEM] = True
    system = Sink()
    inapp = Sink()

    dispatcher = NotificationDispatcher(
        store=store,
        system_notifier=system,
        inapp_notifier=inapp,
        is_app_focused=lambda: False,
    )

    dispatcher.dispatch(Notification(type=NotificationType.PRAZO_PROXIMO, title="t", body="b"))
    assert len(system.calls) == 1
    assert len(inapp.calls) == 0
