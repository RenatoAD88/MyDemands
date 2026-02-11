from pathlib import Path


def test_app_does_not_reference_undefined_export_btn_in_tab1():
    src = Path('app.py').read_text(encoding='utf-8')
    assert 'top.addWidget(export_btn)' not in src
