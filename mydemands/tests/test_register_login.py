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


def test_hash_password_fallback_quando_bcrypt_indisponivel(monkeypatch):
    from mydemands.services import auth_service

    monkeypatch.setattr(auth_service, "bcrypt", None)
    hashed = auth_service.hash_password("Abcdef1!")

    assert hashed.startswith(auth_service.PBKDF2_PREFIX)
    assert auth_service.verify_password("Abcdef1!", hashed)
    assert not auth_service.verify_password("errada", hashed)


def test_verify_password_bcrypt_hash_sem_bcrypt_retorna_false(monkeypatch):
    from mydemands.services import auth_service

    monkeypatch.setattr(auth_service, "bcrypt", None)
    assert not auth_service.verify_password("qualquer", "$2b$12$abcdefghijklmnopqrstuv")
