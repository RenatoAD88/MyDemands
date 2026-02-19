from pathlib import Path

from ui_theme import _read_qss, build_app_stylesheet


def test_read_qss_dev_paths(tmp_path, monkeypatch):
    styles_dir = tmp_path / "mydemands" / "ui" / "styles"
    styles_dir.mkdir(parents=True)
    (styles_dir / "base.qss").write_text("QWidget { color: #111; }", encoding="utf-8")

    monkeypatch.setattr("ui_theme._styles_dir", lambda: styles_dir)

    assert _read_qss("base.qss") == "QWidget { color: #111; }"


def test_build_stylesheet_light_dark_returns_text(tmp_path, monkeypatch):
    styles_dir = tmp_path / "mydemands" / "ui" / "styles"
    styles_dir.mkdir(parents=True)
    (styles_dir / "base.qss").write_text("QWidget { font-size: 13px; }", encoding="utf-8")
    (styles_dir / "light_colors.qss").write_text("QWidget { color: #111827; }", encoding="utf-8")
    (styles_dir / "dark_colors.qss").write_text("QWidget { color: #f9fafb; }", encoding="utf-8")

    monkeypatch.setattr("ui_theme._styles_dir", lambda: Path(styles_dir))

    light_css = build_app_stylesheet("light")
    dark_css = build_app_stylesheet("dark")

    assert isinstance(light_css, str)
    assert isinstance(dark_css, str)
    assert "font-size: 13px;" in light_css
    assert "color: #111827;" in light_css
    assert "color: #f9fafb;" in dark_css
