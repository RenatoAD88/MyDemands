from mydemands.dashboard.eisenhower_dnd import EisenhowerDnDController


def test_quadrant_mapping_payloads():
    controller = EisenhowerDnDController(None)

    assert controller.build_payload_for_target("q1") == {"eisenhower_column": "q1"}
    assert controller.build_payload_for_target("q2") == {"eisenhower_column": "q2"}
    assert controller.build_payload_for_target("q3", {"Prioridade": "Alta"}) == {"eisenhower_column": "q3"}
    assert controller.build_payload_for_target("q4") == {"eisenhower_column": "q4"}


def test_handle_move_calls_executor_once_for_valid_transition():
    calls = []

    def _executor(row, payload):
        calls.append((row, payload))

    controller = EisenhowerDnDController(_executor)
    row = {"_id": "123"}

    controller.handle_move("q4", "q1", row)

    assert calls == [(row, {"eisenhower_column": "q1"})]
