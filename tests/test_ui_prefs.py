from ui_prefs import load_prefs, save_prefs


def test_prefs_roundtrip(tmp_path):
    save_prefs(str(tmp_path), {"tab_index": 2, "q": "abc"})
    assert load_prefs(str(tmp_path)) == {"tab_index": 2, "q": "abc"}


def test_load_prefs_returns_empty_for_missing(tmp_path):
    assert load_prefs(str(tmp_path)) == {}
