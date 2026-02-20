from mydemands.app_controller import AppController
from mydemands.services.user_context import UserContext, current_user, set_current_user


class _FakeQtApp:
    def __init__(self):
        self._quit_called = False
        self._main_win = None

    def quit(self):
        self._quit_called = True


class _FakeMainWindow:
    def __init__(self):
        self.backup_calls = 0
        self.prepare_calls = 0
        self.closed = False
        self.deleted = False

    def save_backup_for_logoff(self):
        self.backup_calls += 1

    def prepare_for_logoff(self):
        self.prepare_calls += 1

    def close(self):
        self.closed = True

    def deleteLater(self):
        self.deleted = True


class _FakeLoginDialog:
    def __init__(self):
        self.visible = False
        self.focused = False

    def show(self):
        self.visible = True

    def raise_(self):
        return None

    def activateWindow(self):
        return None

    def focus_first_field(self):
        self.focused = True

    def close(self):
        self.visible = False

    def deleteLater(self):
        return None


def test_handle_logoff_clears_session_saves_backup_and_returns_to_login(env):
    auth = env["auth"]
    auth.register("user@test.com", "Abcdef1!")
    auth.create_remember_session("user@test.com", ttl_days=1)
    set_current_user(UserContext("user@test.com", "default", "id", env["paths"].base_dir))

    created_logins = []

    def _login_factory():
        login = _FakeLoginDialog()
        created_logins.append(login)
        return login

    app = _FakeQtApp()
    main_window = _FakeMainWindow()
    app._main_win = main_window

    controller = AppController(auth, app, _login_factory)
    controller.register_main_window(main_window)

    controller.handle_logoff()

    assert main_window.backup_calls == 1
    assert env["sessions"].load_session() is None
    assert auth.try_auto_login() is None
    assert current_user() is None
    assert main_window.prepare_calls == 1
    assert main_window.closed is True
    assert main_window.deleted is True
    assert app._main_win is None
    assert app._quit_called is False
    assert len(created_logins) == 1
    assert created_logins[0].visible is True
    assert created_logins[0].focused is True


def test_relogin_reuses_single_main_window_instance(env):
    auth = env["auth"]
    auth.register("user@test.com", "Abcdef1!")

    app = _FakeQtApp()
    opened_windows = []

    controller = AppController(auth, app, lambda: _FakeLoginDialog())

    def _open_main():
        existing = app._main_win
        if existing is not None:
            existing.close()
            existing.deleteLater()
        win = _FakeMainWindow()
        opened_windows.append(win)
        app._main_win = win
        controller.register_main_window(win)

    _open_main()
    first = app._main_win
    assert first is not None

    controller.handle_logoff()
    assert first.closed is True

    _open_main()
    second = app._main_win
    assert second is not None
    assert second is not first
    assert not [w for w in opened_windows if (w is not second and not w.closed)]
