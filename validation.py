from __future__ import annotations

from typing import Dict, List, Optional

from date_field_service import (
    DateFieldError,
    ensure_registration_date_impacts,
    normalize_br_date,
    normalize_deadline_text,
)


class ValidationError(Exception):
    pass


STATUS_OPTIONS = [
    "Não iniciada",
    "Em andamento",
    "Bloqueado",
    "Requer revisão",
    "Concluído",
    "Cancelado",  # compatibilidade
]

PRIORIDADE_OPTIONS = ["Alta", "Média", "Baixa"]
YESNO = ["Sim", "Não"]

REQUIRED_ON_CREATE = {"Descrição", "Prioridade", "Prazo", "Data de Registro", "Status", "Responsável", "Projeto"}
REQUIRED_ON_UPDATE = {"Descrição", "Prioridade", "Prazo", "Data de Registro", "Status", "Responsável", "Projeto"}

DATE_COLUMNS = {"Data de Registro", "Data Conclusão"}
TEXT_COLUMNS = {"Projeto", "Descrição", "Comentário", "ID Azure", "Responsável", "Nome", "Time/Função"}
ENUM_COLUMNS = {
    "Status": STATUS_OPTIONS,
    "Prioridade": PRIORIDADE_OPTIONS,
    "É Urgente?": YESNO,
    "Reportar?": YESNO,
}
PERCENT_COLUMN = "% Conclusão"


def parse_ddmmyyyy_strict(s: str) -> Optional[str]:
    raw = (s or "").strip()
    if not raw:
        return ""
    try:
        return normalize_br_date(raw, field_name="Data")
    except DateFieldError:
        return None


def normalize_prazo_text(s: str) -> str:
    try:
        return normalize_deadline_text(s)
    except DateFieldError as e:
        raise ValidationError(str(e)) from e


def normalize_percent(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    v = v.replace("%", "").replace(",", ".").strip()
    try:
        f = float(v)
    except Exception:
        raise ValidationError("% Conclusão inválido. Use 0..100 ou 0..1.")

    if f > 1.0:
        if f < 0 or f > 100:
            raise ValidationError("% Conclusão fora do intervalo. Use 0..100.")
        f = f / 100.0

    if f < 0 or f > 1:
        raise ValidationError("% Conclusão fora do intervalo. Use 0..100 ou 0..1.")

    return f"{f:.2f}".rstrip("0").rstrip(".") if f != 0 else "0"


def _canonicalize_from_allowed(allowed: List[str], value: str) -> Optional[str]:
    v = (value or "").strip()
    if not v:
        return ""
    m = {a.casefold(): a for a in allowed}
    key = v.casefold()
    if key in m:
        return m[key]
    if v.casefold() == "media" and "Média" in allowed:
        return "Média"
    if v.casefold() == "em espera" and "Bloqueado" in allowed:
        return "Bloqueado"
    return None


def validate_enum(col: str, value: str) -> str:
    allowed = ENUM_COLUMNS[col]
    v = (value or "").strip()
    if not v:
        return ""
    canon = _canonicalize_from_allowed(allowed, v)
    if canon is None:
        raise ValidationError(f"Valor inválido para {col}: '{v}'. Permitidos: {', '.join(allowed)}.")
    return canon


def validate_text(value: str) -> str:
    v = (value or "")
    v = v.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip()
    return v


def validate_date(col: str, value: str) -> str:
    try:
        return normalize_br_date(value, field_name=col)
    except DateFieldError as e:
        raise ValidationError(str(e)) from e


def validate_payload(payload: Dict[str, str], *, mode: str) -> Dict[str, str]:
    if mode not in ("create", "update"):
        raise ValueError("mode inválido")

    if mode == "create":
        for req in REQUIRED_ON_CREATE:
            if not (payload.get(req) or "").strip():
                raise ValidationError(f"Campo obrigatório: {req}.")
    else:
        for req in REQUIRED_ON_UPDATE:
            if req in payload and not (payload.get(req) or "").strip():
                raise ValidationError(f"Campo obrigatório: {req}.")

    normalized: Dict[str, str] = {}

    for k, v in payload.items():
        if k in ENUM_COLUMNS:
            normalized[k] = validate_enum(k, v)
        elif k in DATE_COLUMNS:
            normalized[k] = validate_date(k, v)
        elif k == "Prazo":
            normalized[k] = normalize_prazo_text(v)
        elif k == PERCENT_COLUMN:
            normalized[k] = normalize_percent(v)
        elif k in TEXT_COLUMNS:
            normalized[k] = validate_text(v)
        else:
            normalized[k] = validate_text(v)

    registro = normalized.get("Data de Registro", payload.get("Data de Registro", ""))
    prazo = normalized.get("Prazo", payload.get("Prazo", ""))
    try:
        ensure_registration_date_impacts(registro or "", prazo or "")
    except DateFieldError as e:
        raise ValidationError(str(e)) from e

    return normalized
