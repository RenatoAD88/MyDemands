import sys
import types


def _install_qt_stubs():
    qtwidgets = types.ModuleType("PySide6.QtWidgets")

    class _Dummy:
        Password = 1

        def __init__(self, *args, **kwargs):
            pass

        def setChecked(self, *args, **kwargs):
            pass

        def setStyleSheet(self, *args, **kwargs):
            pass

        def addItems(self, *args, **kwargs):
            pass

        def setCurrentText(self, *args, **kwargs):
            pass

        def setRange(self, *args, **kwargs):
            pass

        def setSingleStep(self, *args, **kwargs):
            pass

        def setValue(self, *args, **kwargs):
            pass

        def setPlaceholderText(self, *args, **kwargs):
            pass

        def setEchoMode(self, *args, **kwargs):
            pass

        def setText(self, *args, **kwargs):
            pass

        @property
        def clicked(self):
            return self

        def connect(self, *args, **kwargs):
            pass

        def addRow(self, *args, **kwargs):
            pass

        def addStretch(self, *args, **kwargs):
            pass

        def addWidget(self, *args, **kwargs):
            pass

        def addLayout(self, *args, **kwargs):
            pass

        def text(self):
            return ""

        def isChecked(self):
            return False

        def value(self):
            return 0.5

    qtwidgets.QCheckBox = _Dummy
    qtwidgets.QComboBox = _Dummy
    qtwidgets.QDialog = _Dummy
    qtwidgets.QFormLayout = _Dummy
    qtwidgets.QHBoxLayout = _Dummy
    qtwidgets.QLabel = _Dummy
    qtwidgets.QLineEdit = _Dummy
    qtwidgets.QMessageBox = _Dummy
    qtwidgets.QPushButton = _Dummy
    qtwidgets.QVBoxLayout = _Dummy
    qtwidgets.QDoubleSpinBox = _Dummy
    qtwidgets.QSpinBox = _Dummy
    qtwidgets.QProgressBar = _Dummy
    qtwidgets.QTextEdit = _Dummy
    qtwidgets.QWidget = _Dummy

    qtgui = types.ModuleType("PySide6.QtGui")

    class _TextOption:
        WrapAtWordBoundaryOrAnywhere = 0

    qtgui.QTextOption = _TextOption

    pyside6 = types.ModuleType("PySide6")
    pyside6.QtWidgets = qtwidgets
    pyside6.QtGui = qtgui

    sys.modules["PySide6"] = pyside6
    sys.modules["PySide6.QtWidgets"] = qtwidgets
    sys.modules["PySide6.QtGui"] = qtgui


_install_qt_stubs()

from ai_writing.settings import AISettings, AISettingsStore


def test_ai_settings_defaults_to_openai_disabled(tmp_path):
    store = AISettingsStore(str(tmp_path))
    loaded = store.load()

    assert loaded.enabled is False
    assert loaded.provider == "openai"



def test_ai_settings_store_persists_last_saved_configuration(tmp_path):
    store = AISettingsStore(str(tmp_path))
    expected = AISettings(
        enabled=False,
        show_chips=False,
        model="meta-llama/Llama-3.1-8B-Instruct",
        temperature=0.9,
        privacy_mode=False,
        debug_log_text=True,
    )

    store.save(expected)
    loaded = store.load()

    assert loaded.enabled is expected.enabled
    assert loaded.show_chips is expected.show_chips
    assert loaded.privacy_mode is expected.privacy_mode
    assert loaded.debug_log_text is expected.debug_log_text


def test_ai_settings_store_persists_provider(tmp_path):
    store = AISettingsStore(str(tmp_path))
    expected = AISettings(provider="openai")

    store.save(expected)
    loaded = store.load()

    assert loaded.provider == "openai"
