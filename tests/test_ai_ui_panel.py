import sys
import types


def _install_qt_stubs():
    qtcore = types.ModuleType("PySide6.QtCore")

    class _QObject:
        def __init__(self, *args, **kwargs):
            pass

    class _Signal:
        def __init__(self, *args, **kwargs):
            pass

        def connect(self, *args, **kwargs):
            pass

        def emit(self, *args, **kwargs):
            pass

    class _QThread:
        def __init__(self, *args, **kwargs):
            self.started = _Signal()

        def start(self):
            pass

        def quit(self):
            pass

    qtcore.QObject = _QObject
    qtcore.QThread = _QThread
    qtcore.Signal = _Signal

    qtwidgets = types.ModuleType("PySide6.QtWidgets")

    class _Widget:
        def __init__(self, *args, **kwargs):
            pass

        def addItem(self, *args, **kwargs):
            pass

        def addItems(self, *args, **kwargs):
            pass

        def addWidget(self, *args, **kwargs):
            pass

        def addLayout(self, *args, **kwargs):
            pass

        def setPlainText(self, *args, **kwargs):
            pass

        def setReadOnly(self, *args, **kwargs):
            pass

        def clicked(self):
            return self

        def connect(self, *args, **kwargs):
            pass

    class _MessageBox:
        warning = staticmethod(lambda *args, **kwargs: None)

    qtwidgets.QComboBox = _Widget
    qtwidgets.QDialog = _Widget
    qtwidgets.QHBoxLayout = _Widget
    qtwidgets.QLabel = _Widget
    qtwidgets.QMessageBox = _MessageBox
    qtwidgets.QPushButton = _Widget
    qtwidgets.QTextEdit = _Widget
    qtwidgets.QVBoxLayout = _Widget
    qtwidgets.QWidget = _Widget

    pyside6 = types.ModuleType("PySide6")
    pyside6.QtCore = qtcore
    pyside6.QtWidgets = qtwidgets

    sys.modules["PySide6"] = pyside6
    sys.modules["PySide6.QtCore"] = qtcore
    sys.modules["PySide6.QtWidgets"] = qtwidgets


_install_qt_stubs()

from ai_writing.ui_panel import AIWritingPanel


class _StatusLabel:
    def __init__(self):
        self.text = ""

    def setText(self, text: str):
        self.text = text


def test_on_error_maps_portuguese_rate_limit_message(monkeypatch):
    panel = AIWritingPanel.__new__(AIWritingPanel)
    panel.status = _StatusLabel()

    captured = {}

    def _fake_warning(_parent, _title, message):
        captured["message"] = message

    monkeypatch.setattr("ai_writing.ui_panel.QMessageBox.warning", _fake_warning)

    panel._on_error("Limite de requisições da OpenAI atingido")

    assert captured["message"] == "Limite de requisições atingido. Tente novamente em instantes."
    assert panel.status.text == "error"
