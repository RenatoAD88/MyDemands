from ai_writing.integration import AIFieldBinding


class FakeCursor:
    def __init__(self, text, start=None, end=None):
        self.text = text
        self.start = start
        self.end = end

    def hasSelection(self):
        return self.start is not None and self.end is not None and self.end > self.start

    def selectedText(self):
        return self.text[self.start:self.end]

    def insertText(self, new_text):
        self.text = self.text[:self.start] + new_text + self.text[self.end:]


class FakeTextWidget:
    def __init__(self, text):
        self._text = text
        self._cursor = FakeCursor(text)

    def toPlainText(self):
        return self._text

    def setPlainText(self, text):
        self._text = text

    def textCursor(self):
        self._cursor.text = self._text
        return self._cursor

    def setTextCursor(self, cursor):
        self._text = cursor.text


def test_selection_replaces_only_selected_text(monkeypatch):
    widget = FakeTextWidget("inicio meio fim")
    widget._cursor = FakeCursor("inicio meio fim", 7, 11)
    binding = AIFieldBinding(widget, lambda: {"field": "Descrição"}, lambda **kwargs: "TROCA")

    class FakePanel:
        Accepted = 1
        def __init__(self, source, handler, context, parent=None):
            self.after = type("A", (), {"toPlainText": lambda self: "TROCA"})()
        def exec(self):
            return 1

    monkeypatch.setattr("ai_writing.integration.PANEL_CLASS", FakePanel)
    binding.open_panel()
    assert widget.toPlainText() == "inicio TROCA fim"


def test_no_selection_replaces_entire_text_and_undo(monkeypatch):
    widget = FakeTextWidget("texto original")
    binding = AIFieldBinding(widget, lambda: {"field": "Comentário"}, lambda **kwargs: "novo")

    class FakePanel:
        Accepted = 1
        def __init__(self, source, handler, context, parent=None):
            self.after = type("A", (), {"toPlainText": lambda self: "novo"})()
        def exec(self):
            return 1

    monkeypatch.setattr("ai_writing.integration.PANEL_CLASS", FakePanel)
    binding.open_panel()
    assert widget.toPlainText() == "novo"
    binding.undo_last()
    assert widget.toPlainText() == "texto original"
