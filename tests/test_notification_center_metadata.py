import pytest
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from notifications.models import Notification, NotificationType
from notifications.store import NotificationStore


EXPECTED_HEADERS = [
    "ID",
    "Descrição da demanda",
    "Data notificação",
    "Tag",
    "Observação",
    "Mensagem",
    "Status",
]


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


def test_notification_center_column_order_headers_and_mapping(tmp_path):
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

    qtcore = __import__("PySide6.QtCore", fromlist=["Qt"])
    Qt = qtcore.Qt
    headers = [dialog.proxy.headerData(i, Qt.Horizontal, Qt.DisplayRole) for i in range(dialog.proxy.columnCount())]
    assert headers == EXPECTED_HEADERS

    assert dialog.proxy.data(dialog.proxy.index(0, 0)) == "D-10"
    assert dialog.proxy.data(dialog.proxy.index(0, 1)).startswith("Uma descrição")
    assert dialog.proxy.data(dialog.proxy.index(0, 2)) == "01/01/2026 11:00"
    assert dialog.proxy.data(dialog.proxy.index(0, 3)) == NotificationType.ALTERACAO_STATUS.value
    assert dialog.proxy.data(dialog.proxy.index(0, 4)) == "Status atualizado"
    assert dialog.proxy.data(dialog.proxy.index(0, 5)) == "Novo status"
    assert dialog.proxy.data(dialog.proxy.index(0, 6)) == "Não lida"

    tooltip_desc = dialog.proxy.data(dialog.proxy.index(0, 1), role=Qt.ToolTipRole)
    assert str(tooltip_desc).startswith("Uma descrição")

    dialog.close()
    app.quit()


def test_notification_center_toggle_read_status_still_works_after_reorder(tmp_path):
    try:
        qtwidgets = __import__("PySide6.QtWidgets", fromlist=["QApplication"])
    except ImportError as exc:
        pytest.skip(f"PySide6 indisponível no ambiente: {exc}")
    QApplication = qtwidgets.QApplication
    app = QApplication.instance() or QApplication([])

    store = NotificationStore(str(tmp_path))
    notif_id = store.insert(
        Notification(
            type=NotificationType.NOVA_DEMANDA,
            title="Demanda",
            body="Corpo",
            timestamp=datetime(2026, 1, 5, 8, 30, 0),
            demand_id="55",
            demand_description="Descrição",
            read=False,
        )
    )

    from notifications.center_view import NotificationCenterDialog

    dialog = NotificationCenterDialog(store, lambda _n: None)
    dialog.refresh()
    dialog.table.selectRow(0)

    assert dialog.proxy.data(dialog.proxy.index(0, 6)) == "Não lida"
    dialog.toggle_selected_read_status()

    updated = store.get_notification_by_id(notif_id)
    assert updated is not None and updated.read is True
    assert dialog.proxy.data(dialog.proxy.index(0, 6)) == "Lida"

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

    assert dialog.proxy.data(dialog.proxy.index(0, 0)) == "—"
    assert dialog.proxy.data(dialog.proxy.index(0, 1)) == "—"

    dialog.close()
    app.quit()
