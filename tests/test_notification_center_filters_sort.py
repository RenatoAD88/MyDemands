import os
import sys
from datetime import datetime

import pytest

Qt = pytest.importorskip("PySide6.QtCore").Qt

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from notifications.center_table import NotificationFilterProxy, NotificationTableModel, notification_column_index
from notifications.models import Notification, NotificationType


@pytest.fixture
def qt_app():
    qtcore = pytest.importorskip("PySide6.QtCore", exc_type=ImportError)
    app = qtcore.QCoreApplication.instance() or qtcore.QCoreApplication([])
    return app


@pytest.fixture
def sample_model(qt_app):
    model = NotificationTableModel()
    model.set_notifications(
        [
            Notification(
                id=1,
                type=NotificationType.NOVA_DEMANDA,
                title="alpha",
                body="Mensagem inicial",
                timestamp=datetime(2026, 1, 1, 10, 0, 0),
                demand_id="2",
                demand_description="Primeira descrição",
                read=False,
            ),
            Notification(
                id=2,
                type=NotificationType.ALTERACAO_STATUS,
                title="Beta",
                body="Outra Mensagem",
                timestamp=datetime(2026, 1, 3, 9, 0, 0),
                demand_id="10",
                demand_description="Segunda descrição",
                read=True,
            ),
            Notification(
                id=3,
                type=NotificationType.MENSAGEM_GERAL_ERRO,
                title="gamma",
                body="Falha genérica",
                timestamp=datetime(2026, 1, 2, 14, 0, 0),
                payload={},
            ),
        ]
    )
    proxy = NotificationFilterProxy()
    proxy.setSourceModel(model)
    return model, proxy


def _visible_ids(model, proxy):
    ids = []
    for row in range(proxy.rowCount()):
        source_row = proxy.mapToSource(proxy.index(row, 0)).row()
        ids.append(model.notification_at(source_row).id)
    return ids


def test_sort_by_date_desc(sample_model):
    model, proxy = sample_model
    proxy.sort(notification_column_index("timestamp"), Qt.DescendingOrder)
    assert _visible_ids(model, proxy) == [2, 3, 1]


def test_sort_by_demand_id_numeric(sample_model):
    model, proxy = sample_model
    proxy.sort(notification_column_index("demand_id"), Qt.AscendingOrder)
    assert _visible_ids(model, proxy) == [3, 1, 2]


def test_sort_by_text_column_case_insensitive(sample_model):
    model, proxy = sample_model
    proxy.sort(notification_column_index("title"), Qt.AscendingOrder)
    assert _visible_ids(model, proxy) == [1, 2, 3]


def test_filter_text_contains_matches(sample_model):
    model, proxy = sample_model
    proxy.set_filter_value("keyword", "mensagem")
    assert _visible_ids(model, proxy) == [1, 2]


def test_filter_numeric_equals(sample_model):
    model, proxy = sample_model
    proxy.set_filter_value("demand_id", "10")
    assert _visible_ids(model, proxy) == [2]


def test_filter_date_range(sample_model):
    model, proxy = sample_model
    proxy.set_filter_value("timestamp_start", datetime(2026, 1, 2, 0, 0, 0))
    proxy.set_filter_value("timestamp_end", datetime(2026, 1, 2, 23, 59, 59))
    assert _visible_ids(model, proxy) == [3]


def test_filter_bool_read_status(sample_model):
    model, proxy = sample_model
    proxy.set_filter_value("read", True)
    assert _visible_ids(model, proxy) == [2]


def test_clear_filters_restores_all_rows(sample_model):
    model, proxy = sample_model
    proxy.set_filter_value("keyword", "alpha")
    assert proxy.rowCount() == 0
    proxy.clear_filters()
    assert _visible_ids(model, proxy) == [1, 2, 3]


def test_legacy_notifications_with_missing_fields_do_not_crash_filters(sample_model):
    model, proxy = sample_model
    proxy.set_filter_value("keyword", "descrição")
    assert _visible_ids(model, proxy) == [1, 2]
    proxy.set_filter_value("demand_id", "999")
    assert proxy.rowCount() == 0
