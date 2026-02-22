from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional


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

REQUIRED_ON_CREATE = {"Descrição", "Prioridade", "Status", "Responsável", "Projeto"}
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
    s = (s or "").strip()
    if not s:
        return ""
    try:
        datetime.strptime(s, "%d/%m/%Y")
        return s
    except Exception:
        return None


def normalize_prazo_text(s: str) -> str:
    if not s:
        return ""
    s = str(s).replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace(";", ",").replace("\n", ",")
    parts = [p.strip() for p in s.split(",") if p.strip()]

    valid: List[str] = []
    for p in parts:
        d = parse_ddmmyyyy_strict(p)
        if d is None:
            raise ValidationError(f"Prazo contém data inválida: '{p}'. Use DD/MM/AAAA.")
        if d:
            valid.append(d)

    seen = set()
    out = []
    for x in valid:
        if x not in seen:
            seen.add(x)
            out.append(x)

    return ", ".join(out)


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
    v = (value or "").strip()
    if not v:
        return ""
    ok = parse_ddmmyyyy_strict(v)
    if ok is None:
        raise ValidationError(f"{col} inválida: '{v}'. Use DD/MM/AAAA.")
    return ok


def validate_payload(payload: Dict[str, str], *, mode: str) -> Dict[str, str]:
    if mode not in ("create", "update"):
        raise ValueError("mode inválido")

    if mode == "create":
        if not (payload.get("Data de Registro") or "").strip():
            payload = dict(payload)
            payload["Data de Registro"] = date.today().strftime("%d/%m/%Y")
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

    DemandValidationService.validate(normalized)

    return normalized


class DemandValidationService:
    PRAZO_LT_REGISTRO_MSG = "O prazo não pode ser anterior à data de registro. Ajuste o prazo ou a data de registro."
    CONCLUSAO_LT_REGISTRO_MSG = "A data de conclusão não pode ser anterior à data de registro. Ajuste a data de conclusão ou a data de registro."
    CONCLUIDO_SEM_CONCLUSAO_MSG = "Para marcar como Concluído, informe a data de conclusão."
    CANCELADO_COM_CONCLUSAO_MSG = "Demandas canceladas não devem possuir data de conclusão."

    @staticmethod
    def _parse_date_safe(value: str, field: str) -> Optional[datetime]:
        parsed = parse_ddmmyyyy_strict(value)
        if parsed is None:
            raise ValidationError(f"{field} inválida: '{(value or '').strip()}'. Use DD/MM/AAAA.")
        if not parsed:
            return None
        return datetime.strptime(parsed, "%d/%m/%Y")

    @staticmethod
    def _parse_prazo_dates(value: str) -> List[datetime]:
        normalized = normalize_prazo_text(value or "")
        out: List[datetime] = []
        for part in [x.strip() for x in normalized.split(",") if x.strip()]:
            out.append(datetime.strptime(part, "%d/%m/%Y"))
        return out

    @classmethod
    def validate(cls, payload: Dict[str, str]) -> None:
        registro = cls._parse_date_safe(payload.get("Data de Registro", ""), "Data de Registro")
        if registro is None:
            raise ValidationError("Campo obrigatório: Data de Registro.")

        conclusao = cls._parse_date_safe(payload.get("Data Conclusão", ""), "Data Conclusão")
        status = (payload.get("Status") or "").strip()
        prazo_dates = cls._parse_prazo_dates(payload.get("Prazo", ""))

        if prazo_dates and min(prazo_dates) < registro:
            raise ValidationError(cls.PRAZO_LT_REGISTRO_MSG)

        if conclusao and conclusao < registro:
            raise ValidationError(cls.CONCLUSAO_LT_REGISTRO_MSG)

        if status == "Concluído" and not conclusao:
            raise ValidationError(cls.CONCLUIDO_SEM_CONCLUSAO_MSG)

        if status == "Cancelado" and conclusao:
            raise ValidationError(cls.CANCELADO_COM_CONCLUSAO_MSG)
