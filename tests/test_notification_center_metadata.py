import pytest
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from notifications.models import Notification, NotificationType
from notifications.store import NotificationStore


def test_notification_payload_contains_demand_id_and_description_when_created(tmp_path):
    store = NotificationStore(str(tmp_path))
    notif_id = store.insert(
        Notification(
            type=NotificationType.NOVA_DEMANDA,
            title="Nova demanda atribuída",
            body="Demanda criada",
            timestamp=datetime(2026, 1, 1, 10, 0, 0),
            demand_id="321",
            demand_description="Descrição snapshot",
        )
    )

    saved = store.get_notification_by_id(notif_id)
    assert saved is not None
    assert saved.demand_id == "321"
    assert saved.demand_description == "Descrição snapshot"
    assert saved.payload.get("demand_id") == "321"
    assert saved.payload.get("demand_description") == "Descrição snapshot"


def test_notification_center_renders_id_and_description(tmp_path):
    try:
        qtwidgets = __import__("PySide6.QtWidgets", fromlist=["QApplication"])
    except ImportError as exc:
        pytest.skip(f"PySide6 indisponível no ambiente: {exc}")
    QApplication = qtwidgets.QApplication
    app = QApplication.instance() or QApplication([])

    store = NotificationStore(str(tmp_path))
    store.insert(
        Notification(
            type=NotificationType.ALTERACAO_STATUS,
            title="Status atualizado",
            body="Novo status",
            timestamp=datetime(2026, 1, 1, 11, 0, 0),
            demand_id="D-10",
            demand_description="Uma descrição muito longa para validar renderização com reticências no grid",
        )
    )

    from notifications.center_view import NotificationCenterDialog

    dialog = NotificationCenterDialog(store, lambda _n: None)
    dialog.refresh()

    headers = [dialog.table.horizontalHeaderItem(i).text() for i in range(dialog.table.columnCount())]
    assert "ID" in headers
    assert "Descrição" in headers

    assert dialog.table.item(0, 3).text() == "D-10"
    rendered_desc = dialog.table.item(0, 4).text()
    assert rendered_desc
    assert dialog.table.item(0, 4).toolTip().startswith("Uma descrição")

    dialog.close()
    app.quit()


def test_legacy_notification_without_fields_does_not_crash(tmp_path):
    try:
        qtwidgets = __import__("PySide6.QtWidgets", fromlist=["QApplication"])
    except ImportError as exc:
        pytest.skip(f"PySide6 indisponível no ambiente: {exc}")
    QApplication = qtwidgets.QApplication
    app = QApplication.instance() or QApplication([])

    store = NotificationStore(str(tmp_path))
    store.insert(
        Notification(
            type=NotificationType.MENSAGEM_GERAL_ERRO,
            title="Erro",
            body="Falha genérica",
            timestamp=datetime(2026, 1, 1, 12, 0, 0),
        )
    )

    from notifications.center_view import NotificationCenterDialog

    dialog = NotificationCenterDialog(store, lambda _n: None)
    dialog.refresh()

    assert dialog.table.item(0, 3).text() == "—"
    assert dialog.table.item(0, 4).text() == "—"

    dialog.close()
    app.quit()
