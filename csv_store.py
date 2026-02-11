from __future__ import annotations

import csv
import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional, Dict, Any

from validation import validate_payload, normalize_prazo_text, ValidationError

CSV_NAME = "data.csv"
DELIMITER = ";"

DISPLAY_COLUMNS = [
    "ID",
    "É Urgente?",
    "Status",
    "Timing",
    "Prioridade",
    "Data de Registro",
    "Prazo",
    "Data Conclusão",
    "Projeto",
    "Descrição",
    "ID Azure",
    "% Conclusão",
    "Responsável",
    "Reportar?",
    "Nome",
    "Time/Função",
]

CSV_COLUMNS = [
    "_id",
    "É Urgente?",
    "Status",
    "Prioridade",
    "Data de Registro",
    "Prazo",
    "Data Conclusão",
    "Projeto",
    "Descrição",
    "ID Azure",
    "% Conclusão",
    "Responsável",
    "Reportar?",
    "Nome",
    "Time/Função",
]

LEGACY_TO_NEW = {
    "Urgente": "É Urgente?",
    "Data Entrada": "Data de Registro",
    "Data Entrega": "Data Conclusão",
}


def _map_legacy_keys(payload: Dict[str, str]) -> Dict[str, str]:
    if not payload:
        return payload
    p = dict(payload)
    for old, new in LEGACY_TO_NEW.items():
        if old in p and new not in p:
            p[new] = p.get(old, "")
    return p


def parse_ddmmyyyy(s: str) -> Optional[date]:
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except Exception:
        return None


def parse_prazos_list(prazo_text: str) -> List[date]:
    prazo_text = normalize_prazo_text(prazo_text or "")
    if not prazo_text:
        return []
    out: List[date] = []
    for p in [x.strip() for x in prazo_text.split(",") if x.strip()]:
        d = parse_ddmmyyyy(p)
        if d:
            out.append(d)
    return sorted(set(out))


def priority_rank(p: str) -> int:
    p = (p or "").strip().lower()
    if p == "alta":
        return 0
    if p in ("média", "media"):
        return 1
    if p == "baixa":
        return 2
    return 9


def percent_is_100(stored: str) -> bool:
    v = (stored or "").strip()
    if not v:
        return False
    try:
        f = float(v.replace(",", ".").replace("%", ""))
    except Exception:
        return False
    if f > 1.0 and f <= 100:
        f = f / 100.0
    return abs(f - 1.0) < 1e-9


def calc_timing(status: str, prazos: List[date], conclusao: Optional[date], today: date) -> str:
    st = (status or "").strip().lower()

    if st == "cancelado":
        return "Cancelado"

    if not prazos:
        return "Sem Prazo Definido"

    # Em aberto
    if st not in ("concluído", "concluido", "cancelado"):
        # regra: se alguma data do prazo é hoje, é Dentro do Prazo
        if today in prazos:
            return "Dentro do Prazo"
        if min(prazos) < today and conclusao is None:
            return "Em Atraso"
        return "Dentro do Prazo"

    # Concluído
    if conclusao is None:
        return "Concluído"

    p = min(prazos)
    if conclusao > p:
        return "Concluída com Atraso"
    if conclusao == p:
        return "Concluída no Prazo"
    return "Concluída antes do Prazo"


def percent_display(stored: str) -> str:
    v = (stored or "").strip()
    if not v:
        return ""
    try:
        f = float(v.replace(",", ".").replace("%", ""))
    except Exception:
        return ""
    if f > 1.0 and f <= 100:
        f = f / 100.0
    steps = [0.0, 0.25, 0.5, 0.75, 1.0]
    closest = min(steps, key=lambda s: abs(s - f))
    return f"{int(round(closest * 100))}%"


def prazo_display(raw_prazo: str) -> str:
    p = normalize_prazo_text(raw_prazo or "")
    if not p:
        return ""
    parts = [x.strip() for x in p.split(",") if x.strip()]
    if len(parts) <= 1:
        return parts[0] if parts else ""
    return "\n".join(
        f"{x}*{',' if i < len(parts) - 1 else ''}"
        for i, x in enumerate(parts)
    )


def _require_conclusao_date_if_needed(status: str, perc: str, concl: str):
    """
    Regras novas (integridade):
    - Se status == Concluído => Data Conclusão obrigatória
    - Se % == 1 => Data Conclusão obrigatória
    """
    st = (status or "").strip()
    concl = (concl or "").strip()
    if st == "Concluído" and not concl:
        raise ValidationError("Para Status = Concluído, o campo Data Conclusão é obrigatório.")
    if percent_is_100(perc or "") and not concl:
        raise ValidationError("Para % Conclusão = 100%, o campo Data Conclusão é obrigatório.")


def _autofix_consistency(payload: Dict[str, str]) -> Dict[str, str]:
    """
    Automação de consistência:
    - Se Data Conclusão preenchida => Status = Concluído e % = 1
    - Se Status = Concluído => % = 1
    - Se % = 1 => Status = Concluído
    """
    p = dict(payload)

    concl = (p.get("Data Conclusão") or "").strip()
    status = (p.get("Status") or "").strip()
    perc = (p.get("% Conclusão") or "").strip()

    if concl:
        p["Status"] = "Concluído"
        p["% Conclusão"] = "1"
        return p

    if status == "Concluído":
        p["% Conclusão"] = "1"

    if percent_is_100(perc):
        p["Status"] = "Concluído"
        p["% Conclusão"] = "1"

    return p


@dataclass
class DemandRow:
    _id: str
    data: Dict[str, str]


class CsvStore:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.csv_path = os.path.join(base_dir, CSV_NAME)
        self.rows: List[DemandRow] = []
        self.load()

    def ensure_exists(self):
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, delimiter=DELIMITER)
                w.writeheader()

    def load(self):
        self.ensure_exists()
        self.rows = []
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            r = csv.DictReader(f, delimiter=DELIMITER)
            for row in r:
                for old, new in LEGACY_TO_NEW.items():
                    if old in row and new not in row:
                        row[new] = row.get(old, "")

                _id = row.get("_id") or str(uuid.uuid4())
                row["_id"] = _id

                for c in CSV_COLUMNS:
                    row.setdefault(c, "")

                row["Prazo"] = normalize_prazo_text(row.get("Prazo", ""))
                self.rows.append(DemandRow(_id=_id, data=row))

        self.save()

    def _atomic_save(self):
        tmp = self.csv_path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, delimiter=DELIMITER)
            w.writeheader()
            for dr in self.rows:
                w.writerow({c: dr.data.get(c, "") for c in CSV_COLUMNS})
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.csv_path)

    def save(self):
        for dr in self.rows:
            dr.data["Prazo"] = normalize_prazo_text(dr.data.get("Prazo", ""))
        self._atomic_save()

    def add(self, payload: Dict[str, str]) -> str:
        payload = _map_legacy_keys(payload)
        payload = validate_payload(payload, mode="create")

        payload = _autofix_consistency(payload)

        _require_conclusao_date_if_needed(
            payload.get("Status", ""),
            payload.get("% Conclusão", ""),
            payload.get("Data Conclusão", ""),
        )

        _id = str(uuid.uuid4())
        row = {c: "" for c in CSV_COLUMNS}
        row["_id"] = _id
        for k, v in payload.items():
            if k in row:
                row[k] = v if v is not None else ""
        row["Prazo"] = normalize_prazo_text(row.get("Prazo", ""))

        self.rows.append(DemandRow(_id=_id, data=row))
        self.save()
        return _id

    def update(self, _id: str, changes: Dict[str, str]) -> None:
        changes = _map_legacy_keys(changes)
        changes = validate_payload(changes, mode="update")

        # encontra registro atual
        dr = self.get(_id)
        if not dr:
            raise ValueError("Registro não encontrado")

        # aplica mudanças em uma cópia para validar consistência
        merged = dict(dr.data)
        merged.update({k: (v if v is not None else "") for k, v in changes.items()})

        merged = _autofix_consistency(merged)

        _require_conclusao_date_if_needed(
            merged.get("Status", ""),
            merged.get("% Conclusão", ""),
            merged.get("Data Conclusão", ""),
        )

        # grava de fato
        dr.data.update(merged)
        if "Prazo" in merged:
            dr.data["Prazo"] = normalize_prazo_text(dr.data.get("Prazo", ""))

        self.save()

    def get(self, _id: str) -> Optional[DemandRow]:
        for dr in self.rows:
            if dr._id == _id:
                return dr
        return None

    def delete_by_id(self, _id: str) -> bool:
        dr = self.get(_id)
        if dr and (dr.data.get("Status") or "").strip() == "Concluído":
            return False

        before = len(self.rows)
        self.rows = [r for r in self.rows if r._id != _id]
        if len(self.rows) == before:
            return False
        self.save()
        return True
        
    def delete_by_line(self, line: int) -> bool:
        """
        Exclui pelo 'ID' conforme exibido na UI (ordem do build_view()).
        Retorna False se a linha for inválida ou se a demanda não puder ser excluída.
        """
        try:
            line = int(line)
        except Exception:
            return False

        if line < 1:
            return False

        # garante estado atualizado
        self.load()

        view = self.build_view()
        if line > len(view):
            return False

        _id = view[line - 1].get("_id")
        if not _id:
            return False

        # delete_by_id já bloqueia concluído
        return self.delete_by_id(_id)

    def _sorted(self, demands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def key(d):
            dr_dt = d.get("_data_registro_date") or date(9999, 12, 31)
            return (priority_rank(d.get("Prioridade", "")), dr_dt, d.get("_id", ""))
        return sorted(demands, key=key)

    def build_view(self) -> List[Dict[str, Any]]:
        today = date.today()
        out: List[Dict[str, Any]] = []
        for i, dr in enumerate(self.rows, start=1):
            data = dr.data
            prazos = parse_prazos_list(data.get("Prazo", ""))
            conclusao = parse_ddmmyyyy(data.get("Data Conclusão", ""))
            registro = parse_ddmmyyyy(data.get("Data de Registro", ""))
            timing = calc_timing(data.get("Status", ""), prazos, conclusao, today)

            out.append({
                "_id": dr._id,
                "ID": str(i),
                "É Urgente?": data.get("É Urgente?", ""),
                "Status": data.get("Status", ""),
                "Timing": timing,
                "Prioridade": data.get("Prioridade", ""),
                "Data de Registro": data.get("Data de Registro", ""),
                "Prazo": prazo_display(data.get("Prazo", "")),
                "Data Conclusão": data.get("Data Conclusão", ""),
                "Projeto": data.get("Projeto", ""),
                "Descrição": data.get("Descrição", ""),
                "ID Azure": data.get("ID Azure", ""),
                "% Conclusão": percent_display(data.get("% Conclusão", "")),
                "Responsável": data.get("Responsável", ""),
                "Reportar?": data.get("Reportar?", ""),
                "Nome": data.get("Nome", ""),
                "Time/Função": data.get("Time/Função", ""),
                "_data_registro_date": registro,
                "_prazos_dates": prazos,
                "_conclusao_date": conclusao,
            })
        return self._sorted(out)

    # filtros
    def tab1_by_prazo_date(self, d: date) -> List[Dict[str, Any]]:
        # mantém a regra atual (pendências por data) do seu projeto
        out: List[Dict[str, Any]] = []
        for x in self.build_view():
            if d not in (x.get("_prazos_dates") or []):
                continue
            status = (x.get("Status") or "").strip()
            if status in ("Concluído", "Cancelado"):
                continue
            # adicional: se estiver "concluído-like", também sai
            if (x.get("Data Conclusão") or "").strip() and (x.get("% Conclusão") or "").strip() == "100%":
                continue
            out.append(x)
        return out

    def tab_pending_all(self) -> List[Dict[str, Any]]:
        return [
            x for x in self.build_view()
            if (x.get("Status") or "").strip() not in ("Concluído", "Cancelado")
        ]

    def tab_concluidas_between(self, start: date, end: date) -> List[Dict[str, Any]]:
        out = []
        for x in self.build_view():
            if (x.get("Status") or "").strip() != "Concluído":
                continue
            cd = x.get("_conclusao_date")
            if cd and start <= cd <= end:
                out.append(x)
        return out

    def export_all_to_csv(self, export_path: str, delimiter: str = ",") -> int:
        """
        Exporta todas as demandas existentes para um CSV de saída.
        Retorna a quantidade de linhas exportadas.
        """
        rows = self.build_view()
        with open(export_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=DISPLAY_COLUMNS, delimiter=delimiter)
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col, "") for col in DISPLAY_COLUMNS})
        return len(rows)
