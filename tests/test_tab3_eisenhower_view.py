import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog


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
