from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ai_writing.prompts import ACTIONS, build_instruction


class _Worker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, fn: Callable[..., str], kwargs: Dict[str, Any]):
        super().__init__()
        self.fn = fn
        self.kwargs = kwargs

    def run(self):
        try:
            self.finished.emit(self.fn(**self.kwargs))
        except Exception as exc:
            self.failed.emit(str(exc))


class AIWritingPanel(QDialog):
    def __init__(self, source_text: str, on_generate: Callable[..., str], context: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("✨ Redigir com IA")
        self.source_text = source_text
        self.context = context
        self.on_generate = on_generate
        self.suggestion_text = ""
        self._previous_applied = ""
        self._variation_counter = 0

        self.before = QTextEdit()
        self.before.setReadOnly(True)
        self.before.setPlainText(source_text)

        self.after = QTextEdit()

        self.status = QLabel("idle")

        self.action_combo = QComboBox()
        for key, label in ACTIONS.items():
            self.action_combo.addItem(label, key)

        self.tone = QComboBox()
        self.tone.addItems(["Neutro", "Objetivo", "Formal"])
        self.length = QComboBox()
        self.length.addItems(["Curto", "Médio", "Detalhado"])

        generate_btn = QPushButton("Gerar")
        regenerate_btn = QPushButton("Gerar outra variação")
        apply_btn = QPushButton("Aplicar")
        copy_btn = QPushButton("Copiar")
        undo_btn = QPushButton("Desfazer")

        generate_btn.clicked.connect(self.generate)
        regenerate_btn.clicked.connect(self.generate_variation)
        apply_btn.clicked.connect(self._apply)
        copy_btn.clicked.connect(self._copy)
        undo_btn.clicked.connect(self._undo)

        top = QHBoxLayout()
        top.addWidget(QLabel("Ação"))
        top.addWidget(self.action_combo)
        top.addWidget(QLabel("Tom"))
        top.addWidget(self.tone)
        top.addWidget(QLabel("Tamanho"))
        top.addWidget(self.length)

        actions = QHBoxLayout()
        for b in (generate_btn, regenerate_btn, apply_btn, copy_btn, undo_btn):
            actions.addWidget(b)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(QLabel("Antes"))
        layout.addWidget(self.before)
        layout.addWidget(QLabel("Depois"))
        layout.addWidget(self.after)
        layout.addWidget(self.status)
        layout.addLayout(actions)

    def generate(self):
        self._variation_counter = 0
        self._start_generation(is_variation=False)

    def generate_variation(self):
        self._variation_counter += 1
        self._start_generation(is_variation=True)

    def _start_generation(self, is_variation: bool):
        self.status.setText("loading")
        action = self.action_combo.currentData()
        tone = self.tone.currentText()
        size = self.length.currentText()
        instruction = build_instruction(action, tone=tone, length=size)
        context = dict(self.context or {})
        context.update({
            "action": action,
            "tone": tone,
            "size": size,
            "variation_index": self._variation_counter if is_variation else 0,
            "is_variation": is_variation,
        })
        kwargs = {
            "input_text": self.source_text,
            "instruction": instruction,
            "context": context,
        }
        self._thread = QThread(self)
        self._worker = _Worker(self.on_generate, kwargs)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_success)
        self._worker.failed.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.start()

    def _on_success(self, text: str):
        self.suggestion_text = text
        self.after.setPlainText(text)
        self.status.setText("success")

    def _on_error(self, message: str):
        details = (message or "").strip() or "Erro desconhecido durante a geração com IA"
        QMessageBox.warning(
            self,
            "IA - erro na geração",
            f"Erro recebido da IA:\n{details}\n\nDetalhes completos também foram salvos em Log/openIA_error.txt.",
        )
        self.status.setText("error")

    def _apply(self):
        self._previous_applied = self.source_text
        self.accept()

    def _copy(self):
        QApplication = __import__("PySide6.QtWidgets", fromlist=["QApplication"]).QApplication
        QApplication.clipboard().setText(self.after.toPlainText())

    def _undo(self):
        self.after.setPlainText(self._previous_applied or self.source_text)
