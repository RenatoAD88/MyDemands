from mydemands.domain.password_policy import PasswordPolicy


def test_rejeita_menor_que_6():
    ok, errors = PasswordPolicy.validate("Aa1!")
    assert not ok
    assert any("6" in e for e in errors)


def test_rejeita_sem_classes_obrigatorias():
    ok, errors = PasswordPolicy.validate("abcdef")
    assert not ok
    assert any("maiúscula" in e for e in errors)
    assert any("número" in e for e in errors)
    assert any("especial" in e for e in errors)


def test_aceita_senha_valida():
    ok, errors = PasswordPolicy.validate("Abcdef1!")
    assert ok
    assert errors == []
