from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict
from zoneinfo import ZoneInfo


BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")


def brasilia_now() -> datetime:
    return datetime.now(BRASILIA_TZ)


class NotificationType(str, Enum):
    NOVA_DEMANDA = "NOVA_DEMANDA"
    ALTERACAO_STATUS = "ALTERACAO_STATUS"
    PRAZO_PROXIMO = "PRAZO_PROXIMO"
    PRAZO_ESTOURADO = "PRAZO_ESTOURADO"
    MENSAGEM_GERAL_ERRO = "MENSAGEM_GERAL_ERRO"


class Channel(str, Enum):
    SYSTEM = "SYSTEM"
    IN_APP = "IN_APP"
    SOUND = "SOUND"


@dataclass
class Notification:
    type: NotificationType
    title: str
    body: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=brasilia_now)
    read: bool = False
    id: int | None = None


@dataclass
class Preferences:
    enabled_types: Dict[NotificationType, bool] = field(
        default_factory=lambda: {nt: True for nt in NotificationType}
    )
    enabled_channels: Dict[Channel, bool] = field(
        default_factory=lambda: {
            Channel.SYSTEM: True,
            Channel.IN_APP: True,
            Channel.SOUND: False,
        }
    )
    scheduler_interval_minutes: int = 15
    muted_until_epoch: float = 0.0

    def type_enabled(self, notification_type: NotificationType) -> bool:
        return bool(self.enabled_types.get(notification_type, True))

    def channel_enabled(self, channel: Channel) -> bool:
        return bool(self.enabled_channels.get(channel, False))

    def is_muted(self, now_epoch: float) -> bool:
        return self.muted_until_epoch > now_epoch
