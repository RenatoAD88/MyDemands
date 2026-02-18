from mydemands.domain.password_policy import PasswordPolicy


def test_reset_password_dialog_validates_policy_realtime_unit():
    ok, errors = PasswordPolicy.validate("abc")
    assert ok is False
    assert any("6" in e for e in errors)
    assert any("minúscula" in e for e in errors) is False
    assert any("maiúscula" in e for e in errors)
    assert any("número" in e for e in errors)
    assert any("especial" in e for e in errors)

    ok2, errors2 = PasswordPolicy.validate("Abcdef1!")
    assert ok2 is True
    assert errors2 == []
