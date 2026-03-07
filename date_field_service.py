from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, List, Optional

DATE_FORMAT = "%d/%m/%Y"
REGISTRATION_FIELD = "Data de Registro"
DEADLINE_FIELD = "Prazo"
CONCLUSION_FIELD = "Data Conclusão"


class DateFieldError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedDemandDates:
    registro: Optional[date]
    prazos: List[date]
    conclusao: Optional[date]


def parse_br_date(value: str) -> Optional[date]:
    raw = (value or "").strip().replace("*", "")
    if not raw:
        return None
    try:
        return datetime.strptime(raw, DATE_FORMAT).date()
    except Exception:
        return None


def normalize_br_date(value: str, *, field_name: str) -> str:
    raw = (value or "").strip().replace("*", "")
    if not raw:
        return ""
    parsed = parse_br_date(raw)
    if parsed is None:
        raise DateFieldError(f"{field_name} inválida: '{raw}'. Use DD/MM/AAAA.")
    return parsed.strftime(DATE_FORMAT)


def normalize_deadline_text(value: str) -> str:
    raw = (value or "")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = raw.replace(";", ",").replace("\n", ",")
    parts = [p.strip() for p in raw.split(",") if p.strip()]

    valid: List[str] = []
    for part in parts:
        normalized = normalize_br_date(part, field_name=DEADLINE_FIELD)
        if normalized:
            valid.append(normalized)

    seen = set()
    unique_ordered: List[str] = []
    for item in valid:
        if item not in seen:
            seen.add(item)
            unique_ordered.append(item)
    return ", ".join(unique_ordered)


def parse_deadline_dates(value: str) -> List[date]:
    normalized = normalize_deadline_text(value)
    if not normalized:
        return []
    parsed = [parse_br_date(p.strip()) for p in normalized.split(",") if p.strip()]
    return sorted({d for d in parsed if d is not None})


def parse_all_demand_dates(registro: str, prazo: str, conclusao: str) -> ParsedDemandDates:
    return ParsedDemandDates(
        registro=parse_br_date(registro),
        prazos=parse_deadline_dates(prazo),
        conclusao=parse_br_date(conclusao),
    )


def validate_registration_before_deadlines(registro: str, prazo: str) -> None:
    parsed = parse_all_demand_dates(registro=registro, prazo=prazo, conclusao="")
    if parsed.registro is None or not parsed.prazos:
        return

    menor_prazo = min(parsed.prazos)
    if menor_prazo < parsed.registro:
        raise DateFieldError(
            f"{DEADLINE_FIELD} inválido: prazo {menor_prazo.strftime(DATE_FORMAT)} é anterior à {REGISTRATION_FIELD} {parsed.registro.strftime(DATE_FORMAT)}."
        )


def ensure_registration_date_impacts(registro: str, prazo: str) -> None:
    """Alias semântico usado por fluxos de atualização para revalidar dependências de Data de Registro."""
    validate_registration_before_deadlines(registro, prazo)
