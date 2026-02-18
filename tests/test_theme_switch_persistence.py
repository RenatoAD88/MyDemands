import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import MainWindow
from csv_store import CsvStore
from mydemands.infra.paths import Paths
from mydemands.infra.repositories.user_prefs_repository import UserPrefsRepository
from mydemands.services.theme_service import ThemeService

QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog
QCheckBox = qtwidgets.QCheckBox


def _app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_theme_pref_persists_per_user(tmp_path):
    paths = Paths(base_dir=tmp_path)
    repo = UserPrefsRepository(paths)

    repo.save("a@test.com", {"theme": "dark"})
    repo.save("b@test.com", {"theme": "light"})

    assert repo.load("a@test.com")["theme"] == "dark"
    assert repo.load("b@test.com")["theme"] == "light"


def test_theme_service_apply_updates_app_state(monkeypatch):
    app = _app()
    calls = []

    monkeypatch.setattr(app, "setStyleSheet", lambda s: calls.append(s))
    svc = ThemeService(app)

    svc.apply_theme("dark")

    assert svc.current_theme() == "dark"
    assert calls


def test_system_info_dialog_switch_updates_pref(tmp_path, monkeypatch):
    app = _app()
    paths = Paths(base_dir=tmp_path)
    repo = UserPrefsRepository(paths)
    repo.save("user@test.com", {"theme": "light"})

    theme = ThemeService(app)
    store = CsvStore(str(tmp_path / "data"))
    win = MainWindow(store, logged_user_email="user@test.com", user_prefs_repo=repo, theme_service=theme)

    def fake_exec(dialog):
        cb = next(w for w in dialog.findChildren(QCheckBox) if "Tema" in w.text())
        cb.setChecked(True)
        return QDialog.Accepted

    monkeypatch.setattr(QDialog, "exec", fake_exec)

    win.show_general_information()

    assert repo.load("user@test.com")["theme"] == "dark"
    assert theme.current_theme() == "dark"
