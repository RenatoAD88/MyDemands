from __future__ import annotations

import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow, VISIBLE_COLUMNS
from csv_store import CsvStore

QApplication = qtwidgets.QApplication
Qt = qtcore.Qt


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _payload(**extra):
    payload = {
        "É Urgente?": "Não",
        "Status": "Em andamento",
        "Prioridade": "Média",
        "Data de Registro": "01/02/2026",
        "Prazo": "10/02/2026",
        "Data Conclusão": "",
        "Projeto": "Projeto Registro",
        "Descrição": "Linha",
        "Comentário": "",
        "ID Azure": "AZ-1",
        "% Conclusão": "0.25",
        "Responsável": "Equipe",
        "Reportar?": "Não",
        "Nome": "Fulano",
        "Time/Função": "Dev",
    }
    payload.update(extra)
    return payload


def _col(name: str) -> int:
    return VISIBLE_COLUMNS.index(name)


def test_edicao_inline_por_id_na_visao_pendentes(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload())

    win = MainWindow(store)
    win.refresh_tab3()
    item = win.t3_table.item(0, _col("Projeto"))
    assert str(item.data(Qt.UserRole) or "") == demand_id

    item.setText("Projeto Alterado")
    assert store.get(demand_id).data["Projeto"] == "Projeto Alterado"
    win.close()


def test_edicao_inline_por_id_na_visao_concluidas(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload(Status="Concluído", **{"Data Conclusão": "10/02/2026", "% Conclusão": "1"}))

    win = MainWindow(store)
    win.refresh_tab4()
    item = win.t4_table.item(0, _col("Projeto"))
    assert str(item.data(Qt.UserRole) or "") == demand_id

    item.setText("Concluida Editada")
    assert store.get(demand_id).data["Projeto"] == "Concluida Editada"
    win.close()


def test_edicao_por_id_na_visao_eisenhower(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload(Prioridade="Alta", **{"É Urgente?": "Sim"}))

    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    item = win.t3_table.item(0, _col("Comentário"))
    assert str(item.data(Qt.UserRole) or "") == demand_id
    item.setText("Atualizado no Eisenhower")

    grouped = win.t3_eisenhower_view.last_groups
    flattened = [row for rows in grouped.values() for row in rows]
    row = next(r for r in flattened if r.get("_id") == demand_id)
    assert row.get("Comentário") == "Atualizado no Eisenhower"
    win.close()


def test_recarrega_visao_com_referencia_obsoleta(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    store.add(_payload())

    win = MainWindow(store)
    win.refresh_tab3()

    calls = {"reload": 0, "warn": []}
    monkeypatch.setattr(win, "refresh_all", lambda: calls.__setitem__("reload", calls["reload"] + 1))
    monkeypatch.setattr("app.QMessageBox.warning", lambda *_args: calls["warn"].append(_args[-1]))

    item = win.t3_table.item(0, _col("Data de Registro"))
    item.setData(Qt.UserRole, "id-quebrado")
    item.setText("09/02/2026")

    assert calls["reload"] >= 1
    assert calls["warn"]
    assert "lista será recarregada" in str(calls["warn"][-1]).lower()
    win.close()
