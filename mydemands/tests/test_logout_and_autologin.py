from mydemands.app_controller import AppController
from mydemands.services.user_context import UserContext, current_user, set_current_user


class _FakeQtApp:
    def __init__(self):
        self._quit_called = False

    def topLevelWidgets(self):
        return []

    def quit(self):
        self._quit_called = True


def test_logoff_clears_session_and_exits(env):
    auth = env["auth"]
    auth.register("user@test.com", "Abcdef1!")
    auth.create_remember_session("user@test.com", ttl_days=1)
    set_current_user(UserContext("user@test.com", "default", "id", env["paths"].base_dir))

    app = _FakeQtApp()
    controller = AppController(auth, app)
    controller.logoff_and_exit()

    assert env["sessions"].load_session() is None
    assert auth.try_auto_login() is None
    assert current_user() is None
    assert app._quit_called is True
