from __future__ import annotations

from typing import Dict

ACTIONS: Dict[str, str] = {
    "clear": "Reescrever mais claro",
    "summary": "Resumir",
    "objective": "Mais objetivo",
    "formal": "Mais formal",
    "steps": "Listar passos",
    "acceptance": "Criar critérios de aceite",
}

_PROMPT_TEMPLATES: Dict[str, str] = {
    "clear": "Reescreva o texto para ficar mais claro, direto e fácil de entender.",
    "summary": "Resuma o texto mantendo os pontos essenciais e o contexto da demanda.",
    "objective": "Reescreva em formato mais objetivo, com foco em fatos e entregáveis.",
    "formal": "Reescreva com tom mais formal e profissional.",
    "steps": "Converta o conteúdo em passos numerados e executáveis.",
    "acceptance": "Gere critérios de aceite claros, verificáveis e orientados a resultado.",
}

_CLEAR_REWRITE_PROMPT = (
    "Você é um revisor de texto em português do Brasil (pt-BR). Sua tarefa é reescrever o texto do usuário de forma mais clara e correta. "
    "Corrija erros de digitação e ortografia agressivamente quando fizer sentido (ex.: 'conequitiidade' -> 'conectividade'). "
    "Se o texto for curto, priorize a correção ortográfica e normalização. "
    "Retorne SOMENTE o texto final entre as tags <final> e </final>. Não escreva mais nada."
)

BASE_RULES = (
    "Responda SEMPRE em português do Brasil (pt-BR). "
    "Preserve os termos técnicos originais do usuário (nomes de sistemas, siglas e códigos). "
    "Não invente contexto não informado. "
    "A resposta deve ser apenas o texto sugerido, sem explicações adicionais."
)


def build_instruction(action: str, tone: str = "Neutro", length: str = "Médio") -> str:
    normalized = (action or "").strip().lower()
    if normalized not in _PROMPT_TEMPLATES:
        normalized = "clear"
    if normalized == "clear":
        return (
            f"{_CLEAR_REWRITE_PROMPT} "
            f"Use tom {tone}. "
            f"Tamanho de saída: {length}. "
            "Nunca responda apenas com 'and', 'ok', 'success' ou variações vazias. "
            f"{BASE_RULES}"
        )

    return (
        f"{_PROMPT_TEMPLATES[normalized]} "
        f"Use tom {tone}. "
        f"Tamanho de saída: {length}. "
        f"{BASE_RULES}"
    )
