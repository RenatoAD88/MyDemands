from csv_store import CsvStore


def _payload(desc: str, prioridade: str = "Alta"):
    return {
        "Descrição": desc,
        "Projeto": "Projeto",
        "Prioridade": prioridade,
        "Prazo": "05/02/2026",
        "Data de Registro": "01/02/2026",
        "Status": "Em andamento",
        "Responsável": "R",
    }


def test_ids_do_not_change_after_delete_and_are_not_reused(tmp_path):
    store = CsvStore(str(tmp_path))

    id1 = store.add(_payload("A", "Alta"))
    id2 = store.add(_payload("B", "Média"))
    id3 = store.add(_payload("C", "Baixa"))

    assert {row["ID"] for row in store.build_view()} == {"1", "2", "3"}

    assert store.delete_by_id(id2) is True

    remaining_by_internal_id = {row["_id"]: row["ID"] for row in store.build_view()}
    assert remaining_by_internal_id[id1] == "1"
    assert remaining_by_internal_id[id3] == "3"

    id4 = store.add(_payload("D", "Alta"))
    remaining_by_internal_id = {row["_id"]: row["ID"] for row in store.build_view()}
    assert remaining_by_internal_id[id4] == "4"


def test_new_rows_always_receive_incremented_id(tmp_path):
    store = CsvStore(str(tmp_path))

    first = store.add(_payload("Original"))
    original_row = next(row for row in store.build_view() if row["_id"] == first)
    assert original_row["ID"] == "1"

    duplicate_like_payload = _payload("Original (cópia)")
    duplicated = store.add(duplicate_like_payload)

    duplicated_row = next(row for row in store.build_view() if row["_id"] == duplicated)
    assert duplicated_row["ID"] == "2"
