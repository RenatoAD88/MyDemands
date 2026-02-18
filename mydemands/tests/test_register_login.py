import pytest

from mydemands.services.auth_service import DuplicateEmailError, InvalidCredentialsError


def test_register_cria_default(env):
    user = env["auth"].register("User@Test.com", "Abcdef1!")
    assert user.role == "default"
    saved = env["users"].get_by_email("user@test.com")
    assert saved is not None


def test_register_duplicado_case_insensitive(env):
    env["auth"].register("User@Test.com", "Abcdef1!")
    with pytest.raises(DuplicateEmailError):
        env["auth"].register("user@test.com", "Abcdef1!")


def test_login_sucesso_e_falha(env):
    env["auth"].register("user@test.com", "Abcdef1!")
    assert env["auth"].authenticate("USER@test.com", "Abcdef1!") is not None
    with pytest.raises(InvalidCredentialsError):
        env["auth"].authenticate("user@test.com", "errada")


def test_hash_nao_contem_senha_pura(env):
    env["auth"].register("user@test.com", "Abcdef1!")
    saved = env["users"].get_by_email("user@test.com")
    assert "Abcdef1!" not in saved.password_hash
