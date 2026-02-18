def test_seed_master_cria_usuario(env):
    auth = env["auth"]
    users = env["users"]

    auth.seed_master()
    user = users.get_by_email("renatoaugustod@gmail.com")

    assert user is not None
    assert user.role == "master"


def test_seed_master_idempotente(env):
    auth = env["auth"]
    db = env["db"]

    auth.seed_master()
    auth.seed_master()

    with db.connect() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM users WHERE email = ?", ("renatoaugustod@gmail.com",)).fetchone()["c"]
    assert count == 1
