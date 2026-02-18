from datetime import datetime, timedelta


def test_remember_me_autologin(env):
    auth = env["auth"]
    auth.register("user@test.com", "Abcdef1!")
    auth.create_remember_session("user@test.com", ttl_days=1)
    user = auth.try_auto_login()
    assert user is not None
    assert user.email == "user@test.com"


def test_expiracao_limpa_sessao(env):
    auth = env["auth"]
    auth.register("user@test.com", "Abcdef1!")
    env["sessions"].save_session("user@test.com", "abc", datetime.utcnow() - timedelta(minutes=1))
    user = auth.try_auto_login()
    assert user is None
    assert env["sessions"].load_session() is None
