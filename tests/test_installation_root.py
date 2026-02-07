import bootstrap


def test_resolve_storage_root_uses_windows_default(monkeypatch):
    monkeypatch.setattr(bootstrap.os, "name", "nt", raising=False)
    assert bootstrap.resolve_storage_root("C:/temp/DemandasApp.exe") == bootstrap.WINDOWS_APP_ROOT


def test_ensure_storage_root_creates_missing_directory(tmp_path):
    target = tmp_path / "MyDemands"

    result = bootstrap.ensure_storage_root(str(target))

    assert result == str(target)
    assert target.is_dir()


def test_ensure_storage_root_returns_none_when_creation_fails(monkeypatch):
    def explode(*args, **kwargs):
        raise OSError("no permission")

    monkeypatch.setattr(bootstrap.os, "makedirs", explode)

    result = bootstrap.ensure_storage_root("C:/MyDemands")

    assert result is None
