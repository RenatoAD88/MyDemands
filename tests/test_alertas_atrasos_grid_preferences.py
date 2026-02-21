import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from PySide6.QtCore import Qt

from mydemands.dashboard.demandas_schema_registry import DemandasSchemaRegistry
from mydemands.dashboard.grid_preferences import GridPreferencesService, UserPreferencesStore
from mydemands.dashboard.view import MonitoramentoView

QApplication = qtwidgets.QApplication


class InMemoryStore(UserPreferencesStore):
    def __init__(self):
        self.data = {}

    def load(self, user_id: str):
        return self.data.get(user_id, {"schema_version": 0, "tables": {}})

    def save(self, user_id: str, payload: dict) -> None:
        self.data[user_id] = payload


def _app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _view_and_service():
    _app()
    store = InMemoryStore()
    service = GridPreferencesService(store, DemandasSchemaRegistry())
    view = MonitoramentoView(user_id="user@x", preferences_service=service)
    return view, service


def test_alertas_uses_demandas_schema_registry_columns_and_no_acoes():
    view, _ = _view_and_service()
    headers = [view.alerts_table.horizontalHeaderItem(i).text() for i in range(view.alerts_table.columnCount())]
    expected = [c.label for c in DemandasSchemaRegistry().demand_columns()]
    assert headers == expected
    assert "Ações" not in headers


def test_column_visibility_reflects_user_preferences():
    view, service = _view_and_service()
    prefs = view.alerts_table.extract_preferences()
    for c in prefs["columns"]:
        c["visible"] = c["id"] in {"id", "status"}
    service.save_table_preferences("user@x", view.ALERTAS_TABLE_KEY, prefs)
    view.alerts_table.apply_preferences(service.load_table_preferences("user@x", view.ALERTAS_TABLE_KEY))

    assert view.alerts_table.isColumnHidden(0) is False
    status_idx = next(i for i, c in enumerate(DemandasSchemaRegistry().demand_columns()) if c.id == "status")
    assert view.alerts_table.isColumnHidden(status_idx) is False
    projeto_idx = next(i for i, c in enumerate(DemandasSchemaRegistry().demand_columns()) if c.id == "projeto")
    assert view.alerts_table.isColumnHidden(projeto_idx) is True


def test_resize_reorder_and_sort_are_auto_saved():
    view, service = _view_and_service()
    key = view.ALERTAS_TABLE_KEY

    status_idx = next(i for i, c in enumerate(DemandasSchemaRegistry().demand_columns()) if c.id == "status")
    view.alerts_table.setColumnWidth(status_idx, 333)
    view.alerts_table.horizontalHeader().moveSection(view.alerts_table.horizontalHeader().visualIndex(status_idx), 0)
    view.alerts_table.sortItems(status_idx, Qt.DescendingOrder)

    saved = service.load_table_preferences("user@x", key)
    width = next(c["width"] for c in saved["columns"] if c["id"] == "status")
    order = next(c["order"] for c in saved["columns"] if c["id"] == "status")
    assert width == 333
    assert order == 0
    assert saved["sort"]["id"] == "status"


def test_restore_default_button_resets_preferences():
    view, service = _view_and_service()
    key = view.ALERTAS_TABLE_KEY

    prefs = view.alerts_table.extract_preferences()
    for c in prefs["columns"]:
        c["visible"] = c["id"] == "status"
    service.save_table_preferences("user@x", key, prefs)
    view._restore_alertas_defaults()

    restored = service.load_table_preferences("user@x", key)
    visible = [c["id"] for c in restored["columns"] if c["visible"]]
    assert "id" in visible
    assert "status" in visible
