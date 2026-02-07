from __future__ import annotations

from typing import Any, Dict, List


def filter_rows(
    rows: List[Dict[str, Any]],
    text_query: str = "",
    status: str = "",
    prioridade: str = "",
    responsavel: str = "",
) -> List[Dict[str, Any]]:
    q = (text_query or "").strip().lower()
    st = (status or "").strip()
    pr = (prioridade or "").strip()
    rs = (responsavel or "").strip().lower()

    out: List[Dict[str, Any]] = []
    for row in rows:
        if st and (row.get("Status") or "").strip() != st:
            continue
        if pr and (row.get("Prioridade") or "").strip() != pr:
            continue
        if rs and rs not in (row.get("Responsável") or "").strip().lower():
            continue
        if q:
            hay = " ".join([
                str(row.get("Projeto", "") or ""),
                str(row.get("Descrição", "") or ""),
                str(row.get("Responsável", "") or ""),
            ]).lower()
            if q not in hay:
                continue
        out.append(row)
    return out


def summary_counts(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    pending = 0
    delayed = 0
    concluded = 0
    for row in rows:
        status = (row.get("Status") or "").strip()
        timing = (row.get("Timing") or "").strip().lower()
        if status == "Concluído":
            concluded += 1
        elif status != "Cancelado":
            pending += 1
        if "atras" in timing:
            delayed += 1
    return {"pending": pending, "delayed": delayed, "concluded": concluded}
