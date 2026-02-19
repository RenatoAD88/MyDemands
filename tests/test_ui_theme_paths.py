from ui_theme import _styles_dir


def test_styles_dir_uses_meipass_when_available(monkeypatch, tmp_path):
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False)
    assert _styles_dir() == tmp_path / "mydemands" / "ui" / "styles"
