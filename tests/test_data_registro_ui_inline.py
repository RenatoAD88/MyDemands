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


def _col(col_name: str) -> int:
    return VISIBLE_COLUMNS.index(col_name)


def test_data_registro_inline_em_tabela_filtrada_atualiza_demanda_correta(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    alvo = store.add(_payload(Projeto="Projeto Alvo"))
    outro = store.add(_payload(Projeto="Projeto Outro", **{"Data de Registro": "02/02/2026"}))

    win = MainWindow(store)
    win.t3_projeto.setCurrentText("Projeto Alvo")
    win.refresh_tab3()

    assert win.t3_table.rowCount() == 1
    item = win.t3_table.item(0, _col("Data de Registro"))
    item.setText("05/02/2026")

    assert store.get(alvo).data["Data de Registro"] == "05/02/2026"
    assert store.get(outro).data["Data de Registro"] == "02/02/2026"
    win.close()


def test_data_registro_inline_em_tabela_ordenada_mantem_id_unico(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    primeiro = store.add(_payload(Projeto="Z Projeto"))
    segundo = store.add(_payload(Projeto="A Projeto", **{"Data de Registro": "02/02/2026"}))

    win = MainWindow(store)
    win.refresh_tab3()
    win.t3_table.sortItems(_col("Projeto"))

    row_item = win.t3_table.item(0, _col("Data de Registro"))
    id_visivel = str(win.t3_table.item(0, 0).data(Qt.UserRole) or "")
    assert id_visivel == segundo
    row_item.setText("06/02/2026")

    assert store.get(segundo).data["Data de Registro"] == "06/02/2026"
    assert store.get(primeiro).data["Data de Registro"] == "01/02/2026"
    win.close()


def test_data_registro_reflete_na_visao_eisenhower(tmp_path):
    _get_app()
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload(Prioridade="Alta", **{"É Urgente?": "Sim"}))

    win = MainWindow(store)
    win._set_tab3_view_mode("eisenhower")
    win.refresh_tab3()

    item = win.t3_table.item(0, _col("Data de Registro"))
    item.setText("07/02/2026")

    grouped = win.t3_eisenhower_view.last_groups
    all_rows = [r for rows in grouped.values() for r in rows]
    updated = next(r for r in all_rows if r.get("_id") == demand_id)
    assert updated["Data de Registro"] == "07/02/2026"
    win.close()


def test_data_registro_inline_exibe_erro_amigavel_para_id_invalido(tmp_path, monkeypatch):
    _get_app()
    store = CsvStore(str(tmp_path))
    demand_id = store.add(_payload())

    win = MainWindow(store)
    win.refresh_tab3()

    warnings = []
    monkeypatch.setattr("app.QMessageBox.warning", lambda *_args: warnings.append(_args[-1]))

    item = win.t3_table.item(0, _col("Data de Registro"))
    item.setData(Qt.UserRole, "id-invalido")
    item.setText("08/02/2026")

    assert store.get(demand_id).data["Data de Registro"] == "01/02/2026"
    assert warnings
    assert "Não foi possível localizar a demanda selecionada" in str(warnings[-1])
    win.close()
