import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qttest = pytest.importorskip("PySide6.QtTest", reason="QtTest indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="QtCore indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

from mydemands.dashboard.eisenhower import EisenhowerThemeManager, EisenhowerView
from mydemands.dashboard.eisenhower_classifier import parse_eisenhower_column_map
from mydemands.dashboard.eisenhower_dnd import EisenhowerDnDController


QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog
Qt = qtcore.Qt
QPoint = qtcore.QPoint
QTest = qttest.QTest


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _add_pending(store: CsvStore, **extra):
    payload = {
        "Descrição": "Demanda",
        "Projeto": "Projeto",
        "Prioridade": "Alta",
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "R",
        "% Conclusão": "0.25",
        "É Urgente?": "Não",
    }
    payload.update(extra)
    return store.add(payload)


def test_toggle_persists_user_preference(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.close()

    reloaded = MainWindow(store)
    assert reloaded.t3_view_mode == "eisenhower"
    assert reloaded.t3_views_stack.currentIndex() == 1
    reloaded.close()


def test_eisenhower_card_edit_updates_quadrant(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store, Prioridade="Baixa", **{"É Urgente?": "Não"})
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    before = win.t3_eisenhower_view.last_groups
    assert any(r.get("_id") == row_id for r in before["q4"])

    class _FakeDialog:
        def __init__(self, *args, **kwargs):
            pass

        def setWindowTitle(self, *_):
            return None

        def exec(self):
            return QDialog.Accepted

        def payload(self):
            return {
                "Descrição": "Demanda",
                "Prioridade": "Alta",
                "Status": "Em andamento",
                "Responsável": "R",
                "Projeto": "Projeto",
                "% Conclusão": "0.25",
                "Data Conclusão": "",
                "É Urgente?": "Não",
                "Data de Registro": "01/02/2026",
                "Prazo": "05/02/2026",
                "Comentário": "",
                "ID Azure": "",
                "Reportar?": "",
                "Nome": "",
                "Time/Função": "",
            }

    monkeypatch.setattr("app.NewDemandDialog", _FakeDialog)
    selected = next(r for r in before["q4"] if r.get("_id") == row_id)
    win._open_demand_from_eisenhower_card(selected)

    after = win.t3_eisenhower_view.last_groups
    assert any(r.get("_id") == row_id for r in after["q3"])
    win.close()


def test_eisenhower_hides_concluded_and_cancelled(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    open_id = _add_pending(store)
    _add_pending(store, Status="Concluído", **{"Data Conclusão": "05/02/2026", "% Conclusão": "1"})
    _add_pending(store, Status="Cancelado", **{"% Conclusão": "0"})

    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    grouped = win.t3_eisenhower_view.last_groups
    all_ids = {r.get("_id") for rows in grouped.values() for r in rows}
    assert open_id in all_ids
    assert len(all_ids) == 1
    win.close()


def test_tab3_uses_segmented_view_selector_without_visualizacao_label(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    win = MainWindow(store)

    assert win.t3_view_default_btn.text() == "Visão Padrão"
    assert win.t3_view_eisenhower_btn.text() == "Visão Eisenhower"

    tab_labels = [lbl.text() for lbl in win.tabs.widget(1).findChildren(qtwidgets.QLabel)]
    assert all("Visualização" not in text for text in tab_labels)
    win.close()


def test_eisenhower_columns_expose_expected_color_accent():
    _get_app()
    view = EisenhowerView(lambda *_: None)

    assert view.findChild(qtwidgets.QFrame, "eisenhowerColumn_q1").property("accent")
    assert view.findChild(qtwidgets.QFrame, "eisenhowerColumn_q2").property("accent")
    assert view.findChild(qtwidgets.QFrame, "eisenhowerColumn_q3").property("accent")
    assert view.findChild(qtwidgets.QFrame, "eisenhowerColumn_q4").property("accent")


def test_eisenhower_minicard_applies_multiline_elide():
    _get_app()
    view = EisenhowerView(lambda *_: None)
    rows = [{
        "_id": "1",
        "ID": "1",
        "Descrição": "X" * 240,
        "Status": "Em andamento",
        "Prioridade": "Alta",
        "Timing": "Sem prazo",
        "É Urgente?": "Não",
    }]
    view.set_rows(rows)

    q3_list = view.findChild(qtwidgets.QListWidget, "q3_list")
    card = q3_list.itemWidget(q3_list.item(0))
    description_label = card.findChild(qtwidgets.QLabel, "eisenhowerDescription")
    info_label = card.findChild(qtwidgets.QLabel, "eisenhowerMetaInfo")
    assert description_label is not None
    assert info_label is not None
    assert "Prioridade:" in info_label.text()
    assert "|" not in info_label.text()
    assert "…" in description_label.text() or "..." in description_label.text()
    assert card.minimumHeight() >= 90
    margins = card.layout().contentsMargins()
    assert margins.left() >= 12
    assert margins.right() >= 12


def test_eisenhower_light_mode_uses_contrasting_card_text_and_border():
    _get_app()
    tokens = EisenhowerThemeManager.tokens(is_dark=False)

    assert tokens["q1"]["text_primary"] == "#0f172a"
    assert tokens["q1"]["card_background"] == "rgba(148, 163, 184, 0.30)"
    assert tokens["q1"]["card_border"] == tokens["q1"]["accent"]


def test_eisenhower_theme_switch_updates_card_tokens():
    _get_app()
    view = EisenhowerView(lambda *_: None)
    view.apply_theme("dark")

    q1_list = view.findChild(qtwidgets.QListWidget, "q1_list")
    qss_dark = q1_list.styleSheet()
    assert "background: rgba(148, 163, 184, 0.30)" in qss_dark
    assert "border: 1px solid #dc2626" in qss_dark

    view.apply_theme("light")
    qss_light = q1_list.styleSheet()
    assert "background: rgba(148, 163, 184, 0.30)" in qss_light
    assert "QLabel#eisenhowerDescription {font-size: 13px; font-weight: 650; color: #0f172a;" in qss_light


def test_duplicate_from_eisenhower_keeps_same_user_column(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store)
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    source = store.get(row_id)
    payload = dict(source.data)

    class _FakeDialog:
        def __init__(self, *_args, **_kwargs):
            pass

        def exec(self):
            return QDialog.Accepted

        def payload(self):
            return dict(payload)

    monkeypatch.setattr("app.NewDemandDialog", _FakeDialog)
    user_id = win.logged_user_email or "anonimo"
    win._move_demand_from_eisenhower(dict(source.data) | {"_id": row_id}, {"eisenhower_column": "q1"})

    selected = next(r for r in win.t3_eisenhower_view.last_groups["q1"] if r.get("_id") == row_id)
    win._duplicate_demand_from_row(selected)

    created = [r for r in store.build_view() if r["_id"] != row_id]
    assert len(created) == 1
    copied_map = parse_eisenhower_column_map(created[0].get("eisenhower_column"))
    assert copied_map.get(user_id) == "q1"
    win.close()


def test_single_click_selects_without_opening_modal(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store)
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    calls = []
    monkeypatch.setattr(win, "_open_demand_from_eisenhower_card", lambda row: calls.append(row))
    q3_list = win.t3_eisenhower_view.findChild(qtwidgets.QListWidget, "q3_list")
    card = q3_list.itemWidget(q3_list.item(0))

    QTest.mouseClick(card, Qt.LeftButton)

    assert calls == []
    assert card.property("selected") is True
    win.close()


def test_double_click_opens_modal(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store)
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    calls = []
    monkeypatch.setattr(win, "_open_demand_from_eisenhower_card", lambda row: calls.append(row.get("_id")))
    q3_list = win.t3_eisenhower_view.findChild(qtwidgets.QListWidget, "q3_list")
    card = q3_list.itemWidget(q3_list.item(0))

    QTest.mouseDClick(card, Qt.LeftButton)

    assert len(calls) == 1
    win.close()


def test_context_menu_contains_expected_actions(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store)
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    captured = {}

    def _fake_exec(menu, *_):
        captured["actions"] = [a.text() for a in menu.actions()]
        return None

    monkeypatch.setattr(qtwidgets.QMenu, "exec", _fake_exec)

    q3_list = win.t3_eisenhower_view.findChild(qtwidgets.QListWidget, "q3_list")
    card = q3_list.itemWidget(q3_list.item(0))
    QTest.mouseClick(card, Qt.RightButton, pos=card.rect().center())

    assert captured["actions"] == ["Editar", "Duplicar", "Excluir"]
    win.close()


def test_click_outside_clears_selection(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    _add_pending(store)
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    q3_list = win.t3_eisenhower_view.findChild(qtwidgets.QListWidget, "q3_list")
    card = q3_list.itemWidget(q3_list.item(0))
    QTest.mouseClick(card, Qt.LeftButton)
    assert card.property("selected") is True

    QTest.mouseClick(q3_list.viewport(), Qt.LeftButton, pos=QPoint(q3_list.viewport().width() - 2, q3_list.viewport().height() - 2))

    assert card.property("selected") is False
    win.close()


def test_dark_mode_label_forces_white_text():
    _get_app()
    tokens = EisenhowerThemeManager.tokens(True)
    assert all(v["column_header"] == "#f8fafc" for v in tokens.values())


def test_minicard_styles_include_spacing_and_padding():
    _get_app()
    view = EisenhowerView(lambda *_: None)
    q1_list = view.findChild(qtwidgets.QListWidget, "q1_list")
    sheet = q1_list.styleSheet()
    assert "margin: 2px 0 8px 0" in sheet
    assert "padding: 8px" in sheet


def test_dnd_controller_mappings_and_persistence_call(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store, Prioridade="Baixa", **{"É Urgente?": "Não"})
    win = MainWindow(store)

    calls = []

    class _SpyService:
        def update(self, demand_id, changes):
            calls.append((demand_id, changes))

    win._demand_update_service = _SpyService()
    row = store.get(row_id).data | {"_id": row_id}
    controller = EisenhowerDnDController(win._move_demand_from_eisenhower)

    controller.handle_move("q4", "q1", row)
    controller.handle_move("q1", "q2", row)
    controller.handle_move("q2", "q3", row)

    assert calls[0] == (row_id, {"eisenhower_column": "q1"})
    assert calls[1] == (row_id, {"eisenhower_column": "q2"})
    assert calls[2] == (row_id, {"eisenhower_column": "q3"})

    controller.handle_move("q1", "q3", row | {"Prioridade": "Alta"})
    assert calls[3] == (row_id, {"eisenhower_column": "q3"})
    win.close()


def test_move_from_q4_to_q1_updates_fields_and_refreshes(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store, Prioridade="Baixa", **{"É Urgente?": "Não"})
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    row = store.get(row_id).data | {"_id": row_id}
    assert win._move_demand_from_eisenhower(row, {"eisenhower_column": "q1"}) is True

    updated = store.get(row_id).data
    per_user = parse_eisenhower_column_map(updated.get("eisenhower_column"))
    assert per_user.get("anonimo") == "q1"
    win.close()


def test_move_failure_returns_false_for_visual_rollback(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store)
    win = MainWindow(store)

    class _FailingService:
        def update(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    win._demand_update_service = _FailingService()
    warnings = []
    monkeypatch.setattr("app.QMessageBox.warning", lambda *_: warnings.append(True))

    row = store.get(row_id).data | {"_id": row_id}
    assert win._move_demand_from_eisenhower(row, {"eisenhower_column": "q1"}) is False
    assert warnings
    win.close()


def test_card_tokens_keep_visible_border_light_and_dark():
    light = EisenhowerThemeManager.tokens(False)
    dark = EisenhowerThemeManager.tokens(True)

    assert all(v["card_border"] == "#dbe3f0" for v in light.values())
    assert all(v["card_border"] == "#475569" for v in dark.values())


def test_first_classification_is_automatic_and_manual_move_persists_user_state(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store, Prioridade="Baixa", **{"É Urgente?": "Não", "Timing": "Dentro do Prazo"})
    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    before = win.t3_eisenhower_view.last_groups
    assert any(r.get("_id") == row_id for r in before["q4"])

    row = store.get(row_id).data | {"_id": row_id}
    assert win._move_demand_from_eisenhower(row, {"eisenhower_column": "q1"}) is True
    win.refresh_tab3()

    after = win.t3_eisenhower_view.last_groups
    assert any(r.get("_id") == row_id for r in after["q1"])
    win.close()


def test_eisenhower_column_persists_per_user(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    row_id = _add_pending(store, Prioridade="Baixa", **{"É Urgente?": "Não"})

    user_a = MainWindow(store, logged_user_email="a@local")
    row = store.get(row_id).data | {"_id": row_id}
    assert user_a._move_demand_from_eisenhower(row, {"eisenhower_column": "q1"}) is True
    user_a.close()

    user_b = MainWindow(store, logged_user_email="b@local")
    user_b._set_tab3_view_mode("eisenhower")
    user_b.refresh_tab3()
    grouped_b = user_b.t3_eisenhower_view.last_groups
    assert any(r.get("_id") == row_id for r in grouped_b["q4"])
    user_b.close()

    user_a_reloaded = MainWindow(store, logged_user_email="a@local")
    user_a_reloaded._set_tab3_view_mode("eisenhower")
    user_a_reloaded.refresh_tab3()
    grouped_a = user_a_reloaded.t3_eisenhower_view.last_groups
    assert any(r.get("_id") == row_id for r in grouped_a["q1"])
    user_a_reloaded.close()
