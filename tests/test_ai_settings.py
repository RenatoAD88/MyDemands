import sys
import types


def _install_qt_stubs():
    qtwidgets = types.ModuleType("PySide6.QtWidgets")

    class _Dummy:
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

        def clicked(self, *args, **kwargs):
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

        def isChecked(self):
            return False

        def currentText(self):
            return "gpt-4.1-mini"

        def value(self):
            return 0.3

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

    pyside6 = types.ModuleType("PySide6")
    pyside6.QtWidgets = qtwidgets

    sys.modules["PySide6"] = pyside6
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_qt_stubs()

from ai_writing.settings import AISettings, AISettingsStore


def test_ai_settings_default_model_is_gpt_4_1_mini(tmp_path):
    store = AISettingsStore(str(tmp_path))

    loaded = store.load()

    assert loaded.model == "gpt-4.1-mini"


def test_ai_settings_store_persists_last_saved_configuration(tmp_path):
    store = AISettingsStore(str(tmp_path))
    expected = AISettings(
        enabled=False,
        show_chips=False,
        model="gpt-5.2",
        temperature=0.9,
        privacy_mode=False,
        debug_log_text=True,
    )

    store.save(expected)
    loaded = store.load()

    assert loaded == expected
