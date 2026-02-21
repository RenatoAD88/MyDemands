from mydemands.dashboard.eisenhower_dnd import EisenhowerDnDController


def test_quadrant_mapping_payloads():
    controller = EisenhowerDnDController(None)

    assert controller.build_payload_for_target("q1") == {"É Urgente?": "Sim", "Prioridade": "Alta", "Timing": "Em Atraso"}
    assert controller.build_payload_for_target("q2") == {"É Urgente?": "Sim", "Prioridade": "Baixa", "Timing": "Em Atraso"}
    assert controller.build_payload_for_target("q3") == {"É Urgente?": "Não", "Prioridade": "Média", "Timing": "Dentro do Prazo"}
    assert controller.build_payload_for_target("q4") == {"É Urgente?": "Não", "Prioridade": "Baixa", "Timing": "Dentro do Prazo"}


def test_handle_move_calls_executor_once_for_valid_transition():
    calls = []

    def _executor(row, payload):
        calls.append((row, payload))

    controller = EisenhowerDnDController(_executor)
    row = {"_id": "123"}

    controller.handle_move("q4", "q1", row)

    assert calls == [(row, {"É Urgente?": "Sim", "Prioridade": "Alta", "Timing": "Em Atraso"})]
