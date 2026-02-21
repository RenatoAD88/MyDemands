from __future__ import annotations

from mydemands.dashboard.demandas_schema_registry import DemandasSchemaRegistry
from mydemands.dashboard.grid_preferences import GridPreferencesService, PreferencesNormalizer, UserPreferencesStore


class InMemoryStore(UserPreferencesStore):
    def __init__(self) -> None:
        self.payloads = {}

    def load(self, user_id: str):
        return self.payloads.get(user_id, {"schema_version": 0, "tables": {}})

    def save(self, user_id: str, payload: dict) -> None:
        self.payloads[user_id] = payload


def _service() -> GridPreferencesService:
    return GridPreferencesService(InMemoryStore(), DemandasSchemaRegistry())


def test_restore_after_reload_same_user_and_table_key():
    service = _service()
    user = "user-1"
    key = "monitoring_alertas_atrasos_grid"

    saved = service.save_table_preferences(
        user,
        key,
        {
            "columns": [
                {"id": "id", "visible": True, "order": 0, "width": 123},
                {"id": "status", "visible": True, "order": 1, "width": 222},
            ],
            "sort": {"id": "status", "direction": "desc"},
        },
    )
    loaded = service.load_table_preferences(user, key)

    assert loaded["columns"][0]["width"] == 123
    assert loaded["sort"]["id"] == "status"
    assert saved["sort"]["direction"] == "desc"


def test_reset_to_default_applies_default_columns():
    service = _service()
    user = "user-2"
    key = "monitoring_alertas_atrasos_grid"

    service.save_table_preferences(user, key, {"columns": [{"id": "status", "visible": True, "order": 0, "width": 200}]})
    reset = service.reset_table_preferences(user, key, ["id", "status"])

    visible_ids = [c["id"] for c in reset["columns"] if c["visible"]]
    assert visible_ids == ["id", "status"]


def test_normalizer_prevents_zero_visible_columns():
    table = {"columns": [{"id": "status", "visible": False, "order": 0, "width": 10}]}
    normalized = PreferencesNormalizer().normalize(table, DemandasSchemaRegistry())
    assert any(c["visible"] for c in normalized["columns"])
    assert normalized["columns"][0]["id"] in {"id", "status"}


def test_migration_discards_nonexistent_and_adds_new_columns():
    service = _service()
    store = service.store
    user = "user-3"
    store.save(
        user,
        {
            "schema_version": 1,
            "tables": {
                "monitoring_alertas_atrasos_grid": {
                    "columns": [
                        {"id": "removed_column", "visible": True, "order": 0, "width": 100},
                        {"id": "id", "visible": True, "order": 1, "width": 100},
                    ]
                }
            },
        },
    )

    loaded = service.load_table_preferences(user, "monitoring_alertas_atrasos_grid")
    ids = [c["id"] for c in loaded["columns"]]
    assert "removed_column" not in ids
    assert "status" in ids
