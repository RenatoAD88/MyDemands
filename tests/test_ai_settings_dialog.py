from __future__ import annotations

import sys
import types

from ai_writing.config_store import AIConfigStore, DEFAULT_HF_MODEL, HUGGINGFACE_PROVIDER, OPENAI_PROVIDER


# Minimal Qt stubs to import ai_writing.settings without real PySide6.
qtwidgets = types.ModuleType("PySide6.QtWidgets")


class _Dummy:
    def __init__(self, *args, **kwargs):
        pass


class _MessageBox:
    information = staticmethod(lambda *args, **kwargs: None)
    warning = staticmethod(lambda *args, **kwargs: None)


for name in [
    "QCheckBox",
    "QComboBox",
    "QDialog",
    "QDoubleSpinBox",
    "QFormLayout",
    "QHBoxLayout",
    "QLabel",
    "QLineEdit",
    "QProgressBar",
    "QPushButton",
    "QSpinBox",
    "QTextEdit",
    "QVBoxLayout",
    "QWidget",
]:
    setattr(qtwidgets, name, _Dummy)
qtwidgets.QMessageBox = _MessageBox

qtgui = types.ModuleType("PySide6.QtGui")


class _TextOption:
    WrapAtWordBoundaryOrAnywhere = 0


qtgui.QTextOption = _TextOption

pyside6 = types.ModuleType("PySide6")
pyside6.QtWidgets = qtwidgets
pyside6.QtGui = qtgui
sys.modules.setdefault("PySide6", pyside6)
sys.modules.setdefault("PySide6.QtWidgets", qtwidgets)
sys.modules.setdefault("PySide6.QtGui", qtgui)

from ai_writing.settings import AISettingsDialog


class _TextField:
    def __init__(self, value: str = ""):
        self._value = value

    def text(self):
        return self._value

    def setText(self, value: str):
        self._value = value


class _BoolField:
    def __init__(self, value: bool = False):
        self._value = value

    def isChecked(self):
        return self._value


class _NumField:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class _ProviderCombo:
    def __init__(self, value: str):
        self._value = value

    def currentData(self):
        return self._value


class _FakeProvider:
    def __init__(self):
        self.received = None

    def check_connectivity(self):
        return None


class _FakeFactory:
    created = None

    @staticmethod
    def create(provider, cfg):
        _FakeFactory.created = (provider, cfg)
        return _FakeProvider()


def _build_dialog(tmp_path):
    dlg = AISettingsDialog.__new__(AISettingsDialog)
    dlg.config_store = AIConfigStore(str(tmp_path / "ai"))
    dlg.enabled = _BoolField(True)
    dlg.provider_combo = _ProviderCombo(HUGGINGFACE_PROVIDER)
    dlg.openai_key = _TextField("sk-saved")
    dlg.openai_model = _TextField("gpt-4o-mini")
    dlg.openai_temperature = _NumField(0.7)
    dlg.openai_max_tokens = _NumField(321)
    dlg.hf_token = _TextField("hf-unsaved")
    dlg.hf_model = _TextField("repo/unsaved")
    dlg.hf_temperature = _NumField(0.4)
    dlg.hf_max_tokens = _NumField(222)
    dlg.hf_top_p = _NumField(0.8)
    dlg.hf_timeout = _NumField(19.0)
    dlg.monthly_limit = _NumField(200)
    dlg.cache_enabled = _BoolField(True)
    dlg._provider = lambda: HUGGINGFACE_PROVIDER
    return dlg


def test_test_connection_uses_unsaved_modal_values(tmp_path, monkeypatch):
    dlg = _build_dialog(tmp_path)
    cfg = dlg.config_store.load_config()
    cfg.hf_model = "repo/saved"
    cfg.hf_api_token = "hf-saved"
    dlg.config_store.save_config(cfg)
    config_path = dlg.config_store._config_path()
    original = open(config_path, "r", encoding="utf-8").read()

    monkeypatch.setattr("ai_writing.settings.AIProviderFactory", _FakeFactory)
    monkeypatch.setattr("ai_writing.settings.QMessageBox", _MessageBox)
    dlg._test_connection()

    provider, received_cfg = _FakeFactory.created
    assert provider == HUGGINGFACE_PROVIDER
    assert received_cfg.hf_model == "repo/unsaved"
    assert received_cfg.hf_api_token == "hf-unsaved"

    after = open(config_path, "r", encoding="utf-8").read()
    assert after == original


def test_hf_default_model_prefilled_when_empty(tmp_path):
    dlg = _build_dialog(tmp_path)
    dlg.hf_model = _TextField("")
    dlg._provider = lambda: HUGGINGFACE_PROVIDER

    dlg._ensure_hf_default_model()

    assert dlg.hf_model.text() == DEFAULT_HF_MODEL


def test_save_persists_and_reopen_restores(tmp_path):
    store = AIConfigStore(str(tmp_path / "ai"))
    cfg = store.load_config()
    cfg.ai_provider = HUGGINGFACE_PROVIDER
    cfg.hf_api_token = "hf-token"
    cfg.hf_model = "repo/model"
    store.save_config(cfg)

    loaded = store.load_config()
    assert loaded.ai_provider == HUGGINGFACE_PROVIDER
    assert loaded.hf_api_token == "hf-token"
    assert loaded.hf_model == "repo/model"


def test_openai_help_dialog_opens_and_has_text(monkeypatch):
    dlg = AISettingsDialog.__new__(AISettingsDialog)
    captured = {}

    class _FakeInfoDialog:
        def __init__(self, title, body, parent):
            captured["title"] = title
            captured["body"] = body
            captured["parent"] = parent

        def exec(self):
            captured["executed"] = True

    monkeypatch.setattr("ai_writing.settings.InfoTextDialog", _FakeInfoDialog)

    dlg.open_openai_help_dialog()

    assert captured["title"] == "Como configurar OpenAI"
    assert "API Key" in captured["body"]
    assert captured["body"].strip()
    assert captured["parent"] is dlg
    assert captured.get("executed") is True


def test_hf_help_dialog_opens_and_has_text(monkeypatch):
    dlg = AISettingsDialog.__new__(AISettingsDialog)
    captured = {}

    class _FakeInfoDialog:
        def __init__(self, title, body, parent):
            captured["title"] = title
            captured["body"] = body
            captured["parent"] = parent

        def exec(self):
            captured["executed"] = True

    monkeypatch.setattr("ai_writing.settings.InfoTextDialog", _FakeInfoDialog)

    dlg.open_hf_help_dialog()

    assert captured["title"] == "Como configurar Hugging Face"
    assert "Access Token" in captured["body"]
    assert captured["body"].strip()
    assert captured["parent"] is dlg
    assert captured.get("executed") is True


class _VisibleWidget:
    def __init__(self):
        self.visible = None

    def setVisible(self, value: bool):
        self.visible = value


def test_help_button_visibility_openai():
    dlg = AISettingsDialog.__new__(AISettingsDialog)
    dlg.btn_help_openai = _VisibleWidget()
    dlg.btn_help_hf = _VisibleWidget()

    dlg._update_help_visibility("OpenAI")

    assert dlg.btn_help_openai.visible is True
    assert dlg.btn_help_hf.visible is False


def test_help_button_visibility_huggingface():
    dlg = AISettingsDialog.__new__(AISettingsDialog)
    dlg.btn_help_openai = _VisibleWidget()
    dlg.btn_help_hf = _VisibleWidget()

    dlg._update_help_visibility("Hugging Face")

    assert dlg.btn_help_openai.visible is False
    assert dlg.btn_help_hf.visible is True


def test_help_label_removed():
    settings_source = open("ai_writing/settings.py", "r", encoding="utf-8").read()

    assert 'form.addRow("Ajuda",' not in settings_source
