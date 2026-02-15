from __future__ import annotations

from typing import Any, Callable, Dict

PANEL_CLASS = None


class AIFieldBinding:
    def __init__(self, text_widget: Any, context_provider: Callable[[], Dict[str, Any]], generate_handler):
        self.text_widget = text_widget
        self.context_provider = context_provider
        self.generate_handler = generate_handler
        self._last_original = ""

    def open_panel(self, parent=None):
        cursor = self.text_widget.textCursor()
        has_selection = cursor.hasSelection()
        source = cursor.selectedText() if has_selection else self.text_widget.toPlainText()

        global PANEL_CLASS
        if PANEL_CLASS is None:
            from ai_writing.ui_panel import AIWritingPanel
            PANEL_CLASS = AIWritingPanel

        panel = PANEL_CLASS(source, self.generate_handler, self.context_provider(), parent=parent)
        if panel.exec() != panel.Accepted:
            return

        suggestion = panel.after.toPlainText()
        self._last_original = self.text_widget.toPlainText()
        if has_selection:
            cursor.insertText(suggestion)
            self.text_widget.setTextCursor(cursor)
        else:
            self.text_widget.setPlainText(suggestion)

    def undo_last(self):
        if self._last_original:
            self.text_widget.setPlainText(self._last_original)


def attach_ai_writing(text_widget: Any, context_provider: Callable[[], Dict[str, Any]], generate_handler):
    from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

    binding = AIFieldBinding(text_widget, context_provider, generate_handler)
    wrapper = QWidget()
    layout = QHBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(text_widget)

    btn = QPushButton("✨ Redigir com IA")
    btn.clicked.connect(lambda: binding.open_panel(parent=text_widget.window()))
    layout.addWidget(btn)

    text_widget._ai_binding = binding  # type: ignore[attr-defined]
    text_widget._ai_button = btn  # type: ignore[attr-defined]
    return wrapper


def apply_suggestion_to_widget(text_widget: Any, suggestion: str) -> None:
    cursor = text_widget.textCursor()
    if cursor.hasSelection():
        cursor.insertText(suggestion)
        text_widget.setTextCursor(cursor)
        return
    text_widget.setPlainText(suggestion)
