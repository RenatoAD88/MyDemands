import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from csv_store import CsvStore, DISPLAY_COLUMNS, EXPORT_TEMPLATE_VERSION, EXPORT_VERSION_PREFIX
from validation import ValidationError


def _row(id_value: str, projeto: str):
    row = {k: "" for k in DISPLAY_COLUMNS}
    row["ID"] = id_value
    row["É Urgente?"] = "Não"
    row["Status"] = "Não iniciada"
    row["Prioridade"] = "Média"
    row["Data de Registro"] = "01/01/2025"
    row["Prazo"] = "02/01/2025"
    row["Projeto"] = projeto
    row["Descrição"] = projeto
    row["% Conclusão"] = "0%"
    return row


def _csv_text_with_version(version: str, *rows: dict) -> str:
    body = [",".join(DISPLAY_COLUMNS)]
    for row in rows:
        body.append(",".join([row.get(c, "") for c in DISPLAY_COLUMNS]))
    return f"{EXPORT_VERSION_PREFIX}{version}\n" + "\n".join(body)


def test_import_merge_behavior_rewrites_ids_and_appends_data(tmp_path):
    store = CsvStore(str(tmp_path))
    base = store.parse_exported_csv_text(_csv_text_with_version(EXPORT_TEMPLATE_VERSION, _row("1", "Local")))
    store.replace_with_rows(base)

    incoming_text = _csv_text_with_version(EXPORT_TEMPLATE_VERSION, _row("1", "Importado 1"), _row("2", "Importado 2"))
    imported = store.parse_exported_csv_text(incoming_text)
    store.merge_with_rows(imported)

    rows = store.build_view()
    assert len(rows) == 3
    assert [r["ID"] for r in rows] == ["1", "2", "3"]
    assert [r["Projeto"] for r in rows] == ["Local", "Importado 1", "Importado 2"]


def test_import_replace_clears_existing(tmp_path):
    store = CsvStore(str(tmp_path))
    store.add({"Projeto": "Antigo", "Descrição": "A", "Status": "Não iniciada", "Data de Registro": "01/01/2025", "Prazo": "02/01/2025"})

    incoming_text = _csv_text_with_version(EXPORT_TEMPLATE_VERSION, _row("9", "Novo Só"))
    imported = store.parse_exported_csv_text(incoming_text)
    store.replace_with_rows(imported)

    rows = store.build_view()
    assert len(rows) == 1
    assert rows[0]["Projeto"] == "Novo Só"


def test_import_rejects_template_version_mismatch(tmp_path):
    store = CsvStore(str(tmp_path))
    incoming_text = _csv_text_with_version("999", _row("1", "Incompatível"))

    with pytest.raises(ValidationError, match="Versão de template incompatível"):
        store.parse_exported_csv_text(incoming_text)
