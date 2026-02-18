
def test_logout_removes_persisted_session(env):
    auth = env["auth"]
    auth.register("user@test.com", "Abcdef1!")
    auth.create_remember_session("user@test.com", ttl_days=1)

    assert auth.try_auto_login() is not None

    auth.logout()

    assert env["sessions"].load_session() is None
    assert auth.try_auto_login() is None
