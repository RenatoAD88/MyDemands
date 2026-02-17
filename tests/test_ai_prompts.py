from ai_writing.prompts import build_instruction


def test_build_instruction_ptbr_for_each_chip():
    for action in ["clear", "summary", "objective", "formal", "steps", "acceptance"]:
        instruction = build_instruction(action, tone="Formal", length="Curto")
        assert "português do Brasil" in instruction
        assert "Preserve os termos técnicos" in instruction
        assert "tom Formal" in instruction
        assert "Tamanho de saída: Curto" in instruction


def test_build_instruction_clear_uses_strong_revision_prompt():
    instruction = build_instruction("clear", tone="Neutro", length="Curto")

    assert "revisor de texto em português do Brasil (pt-BR)" in instruction
    assert "<final>" in instruction
    assert "conequitiidade" in instruction
    assert "Nunca responda apenas com 'and'" in instruction
