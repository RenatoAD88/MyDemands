from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Tuple

from csv_store import parse_prazos_list


@dataclass(frozen=True)
class DashboardMetrics:
    total_demandas: int
    concluidas: int
    concluidas_percentual: int
    em_atraso: int
    em_andamento: int
    por_status: Dict[str, int]
    por_prioridade: Dict[str, int]
    alertas: List[Dict[str, str]]


class DashboardMetricsService:
    """Calcula indicadores com cache simples baseado no fingerprint das demandas."""

    def __init__(self) -> None:
        self._last_fingerprint: Tuple[Any, ...] | None = None
        self._last_metrics: DashboardMetrics | None = None

    def calculate(self, rows: Iterable[Dict[str, Any]]) -> DashboardMetrics:
        rows_list = list(rows)
        fingerprint = self._build_fingerprint(rows_list)
        if fingerprint == self._last_fingerprint and self._last_metrics is not None:
            return self._last_metrics

        total = len(rows_list)
        concluidas = 0
        em_andamento = 0
        em_atraso = 0
        por_status: Dict[str, int] = {}
        por_prioridade: Dict[str, int] = {"Alta": 0, "Média": 0, "Baixa": 0}
        alertas: List[Dict[str, str]] = []
        today = date.today()

        for row in rows_list:
            status = str(row.get("Status") or "").strip()
            prioridade = str(row.get("Prioridade") or "").strip()
            projeto = str(row.get("Projeto") or "").strip()
            descricao = str(row.get("Descrição") or "").strip() or "Sem descrição"
            prazo_raw = str(row.get("Prazo") or "")
            demand_id = str(row.get("ID") or "")

            por_status[status] = por_status.get(status, 0) + 1
            if prioridade in por_prioridade:
                por_prioridade[prioridade] += 1

            if status == "Concluído":
                concluidas += 1
            if status == "Em andamento":
                em_andamento += 1

            prazos = parse_prazos_list(prazo_raw)
            if status not in {"Concluído", "Cancelado"} and prazos:
                min_prazo = min(prazos)
                if min_prazo < today:
                    em_atraso += 1
                    alertas.append(
                        {
                            "id": demand_id,
                            "titulo": f"{projeto} — {descricao}" if projeto else descricao,
                            "prazo": min_prazo.strftime("%d/%m/%Y"),
                            "badge": "Atrasada",
                        }
                    )
                elif min_prazo == today:
                    alertas.append(
                        {
                            "id": demand_id,
                            "titulo": f"{projeto} — {descricao}" if projeto else descricao,
                            "prazo": min_prazo.strftime("%d/%m/%Y"),
                            "badge": "Prazo hoje",
                        }
                    )

        percentual = int(round((concluidas / total) * 100)) if total else 0
        metrics = DashboardMetrics(
            total_demandas=total,
            concluidas=concluidas,
            concluidas_percentual=percentual,
            em_atraso=em_atraso,
            em_andamento=em_andamento,
            por_status=por_status,
            por_prioridade=por_prioridade,
            alertas=sorted(alertas, key=lambda x: (x["badge"] != "Atrasada", x["prazo"], x["id"])),
        )
        self._last_fingerprint = fingerprint
        self._last_metrics = metrics
        return metrics

    def _build_fingerprint(self, rows: List[Dict[str, Any]]) -> Tuple[Any, ...]:
        ordered = []
        for row in rows:
            ordered.append(
                (
                    str(row.get("_id") or ""),
                    str(row.get("ID") or ""),
                    str(row.get("Status") or ""),
                    str(row.get("Prioridade") or ""),
                    str(row.get("Prazo") or ""),
                    str(row.get("Projeto") or ""),
                    str(row.get("Descrição") or ""),
                )
            )
        ordered.sort()
        return tuple(ordered)
