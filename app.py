from __future__ import annotations

import csv
import os
import sys
from datetime import date
from typing import Dict, Any, List, Optional, Tuple

from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QColor, QLinearGradient, QGradient, QBrush, QIcon, QKeyEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QToolButton, QFileDialog,
    QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog,
    QDialog, QFormLayout,
    QDateEdit, QLineEdit, QTextEdit, QPlainTextEdit, QComboBox,
    QListWidget, QGroupBox, QAbstractItemView,
    QMenu, QScrollArea
)
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtWidgets import QHeaderView, QStyle
from PySide6.QtWidgets import QSizePolicy

from csv_store import CsvStore, parse_prazos_list
from team_control import TeamControlStore, month_days, participation_for_date, STATUS_COLORS, WEEKDAY_LABELS, build_team_control_report_rows, monthly_k_count, split_member_names
from validation import ValidationError, normalize_prazo_text, validate_payload
from bootstrap import resolve_storage_root, ensure_storage_root
from ui_theme import APP_STYLESHEET, status_color, timing_color
from ui_filters import filter_rows, summary_counts
from ui_prefs import load_prefs, save_prefs
from form_rules import required_fields

EXEC_NAME = os.path.basename(sys.argv[0]).lower()
DEBUG_MODE = "debug" in EXEC_NAME
DATE_FMT_QT = "dd/MM/yyyy"
PRAZO_TODAY_BG = (255, 249, 196)  # amarelo claro
def debug_msg(title: str, text: str):
    if DEBUG_MODE:
        QMessageBox.information(None, title, text)



def qdate_to_date(qd: QDate) -> date:
    return date(qd.year(), qd.month(), qd.day())


def prazo_contains_today(prazo_text: str, today: Optional[date] = None) -> bool:
    if not prazo_text:
        return False
    ref = today or date.today()
    normalized = prazo_text.replace("*", "").replace("\n", ",")
    return ref in parse_prazos_list(normalized)


def selected_member_names(table: QTableWidget) -> List[str]:
    footer_row = table.rowCount() - 1
    names: List[str] = []
    seen_rows = set()

    for idx in table.selectedIndexes():
        row = idx.row()
        if row < 0 or row >= footer_row or row in seen_rows:
            continue

        name_item = table.item(row, 0)
        name = (name_item.text() if name_item else "").strip()
        if not name:
            continue

        names.append(name)
        seen_rows.add(row)

    return names


def selected_members_with_ids(table: QTableWidget) -> List[Tuple[str, str]]:
    footer_row = table.rowCount() - 1
    members: List[Tuple[str, str]] = []
    seen_rows = set()

    for idx in table.selectedIndexes():
        row = idx.row()
        if row < 0 or row >= footer_row or row in seen_rows:
            continue

        name_item = table.item(row, 0)
        member_name = (name_item.text() if name_item else "").strip()
        member_id = str(name_item.data(Qt.UserRole) if name_item else "").strip()
        if not member_name or not member_id:
            continue

        members.append((member_id, member_name))
        seen_rows.add(row)

    return members


VISIBLE_COLUMNS = [
    "ID", "É Urgente?", "Status", "Timing", "Prioridade",
    "Data de Registro", "Prazo", "Data Conclusão",
    "Projeto", "Descrição", "ID Azure", "% Conclusão",
    "Responsável", "Reportar?", "Nome", "Time/Função"
]

# Campos que só podem ser editados via picker
PICKER_ONLY = {"Data de Registro", "Prazo", "Data Conclusão"}

# Timing e ID não editáveis
NON_EDITABLE = {"ID", "Timing"} | PICKER_ONLY
DESC_COLUMN_MAX_CHARS = 45

STATUS_EDIT_OPTIONS = [
    "Não iniciada",
    "Em andamento",
    "Em espera",
    "Requer revisão",
    "Concluído",
]
PRIORIDADE_EDIT_OPTIONS = ["Alta", "Média", "Baixa"]
URGENCIA_EDIT_OPTIONS = ["Sim", "Não"]
REPORTAR_EDIT_OPTIONS = ["Sim", "Não"]

# ✅ % Conclusão como combo fixo
PERCENT_COMBO_OPTIONS = ["0%", "25%", "50%", "75%", "100%"]

PERCENT_OPTIONS: List[Tuple[str, str]] = [
    ("", ""),
    ("0% - Não iniciado", "0"),
    ("25% - Começando", "0.25"),
    ("50% - Parcial", "0.5"),
    ("75% - Avançado", "0.75"),
    ("100% - Concluído", "1"),
]

PERCENT_QUICK_PICK = [
    ("0%", "0"),
    ("25%", "0.25"),
    ("50%", "0.5"),
    ("75%", "0.75"),
]

PRIORIDADE_TEXT_COLORS: Dict[str, Tuple[int, int, int]] = {
    "alta": (220, 38, 38),   # vermelho
    "média": (202, 138, 4),  # amarelo
    "media": (202, 138, 4),  # fallback sem acento
    "baixa": (22, 163, 74),  # verde
}

PROGRESS_FILL_COLOR = (3, 141, 220)


def _app_icon_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "icondemand.png")


def _normalize_percent_to_decimal_str(raw: str) -> str:
    """
    Converte entradas comuns em string decimal:
    - "100%" -> "1"
    - "100" -> "1"
    - "1" / "1.0" -> "1"
    - "0,75" -> "0.75"
    Retorna "" se não conseguir.
    """
    s = (raw or "").strip()
    if not s:
        return ""
    s2 = s.replace(" ", "").replace(",", ".")
    if s2.endswith("%"):
        s2 = s2[:-1]
    try:
        f = float(s2)
    except Exception:
        return ""
    if f > 1.0 and f <= 100.0:
        f = f / 100.0

    # normaliza para degraus conhecidos
    steps = [0.0, 0.25, 0.5, 0.75, 1.0]
    closest = min(steps, key=lambda x: abs(x - f))
    if abs(closest - f) < 1e-6:
        f = closest

    if abs(f - 1.0) < 1e-9:
        return "1"
    if abs(f - 0.0) < 1e-9:
        return "0"
    return str(f).rstrip("0").rstrip(".") if "." in str(f) else str(f)


def _is_percent_100(raw: str) -> bool:
    return _normalize_percent_to_decimal_str(raw) == "1"


def _percent_to_fraction(raw: str) -> Optional[float]:
    normalized = _normalize_percent_to_decimal_str(raw)
    if not normalized:
        return None
    try:
        value = float(normalized)
    except Exception:
        return None
    return max(0.0, min(1.0, value))


class ColumnComboDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, column_to_options: Dict[int, List[str]] | None = None):
        super().__init__(parent)
        self.column_to_options = column_to_options or {}

    def createEditor(self, parent, option, index):
        col = index.column()
        if col in self.column_to_options:
            combo = QComboBox(parent)
            combo.setEditable(False)
            items = self.column_to_options[col]
            combo.addItems(items)
            combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

            if items:
                text_width = max(combo.fontMetrics().horizontalAdvance(item) for item in items)
                popup_width = text_width + 36  # folga para padding, borda e barra de rolagem
                combo.view().setMinimumWidth(popup_width)
            return combo
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        col = index.column()
        if col in self.column_to_options and isinstance(editor, QComboBox):
            current = (index.data(Qt.EditRole) or "").strip()
            items = self.column_to_options[col]
            try:
                idx = items.index(current)
            except ValueError:
                # se vier vazio, cai no primeiro
                idx = 0
            editor.setCurrentIndex(idx)
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        col = index.column()
        if col in self.column_to_options and isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.EditRole)
            return
        super().setModelData(editor, model, index)


class TeamSectionTable(QTableWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._bulk_edit_handler = None

    def set_bulk_edit_handler(self, handler):
        self._bulk_edit_handler = handler

    def keyPressEvent(self, event: QKeyEvent):
        if not callable(self._bulk_edit_handler):
            return super().keyPressEvent(event)

        key = event.key()
        text = (event.text() or "").strip().upper()
        code: Optional[str] = None
        if key in {Qt.Key_Delete, Qt.Key_Backspace}:
            code = ""
        elif len(text) == 1 and text in STATUS_COLORS:
            code = text

        if code is None:
            return super().keyPressEvent(event)

        if self._bulk_edit_handler(self, self.selectedIndexes(), code):
            event.accept()
            return

        super().keyPressEvent(event)

    def fit_height_to_rows(self):
        self.resizeRowsToContents()
        rows_height = sum(self.rowHeight(row) for row in range(self.rowCount()))
        headers_height = self.horizontalHeader().height() if self.horizontalHeader() else 0
        frame_height = self.frameWidth() * 2
        total_height = rows_height + headers_height + frame_height
        self.setMinimumHeight(total_height)
        self.setMaximumHeight(total_height)


class BaseModalDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._primary_btn: Optional[QPushButton] = None
        self._cancel_btn: Optional[QPushButton] = None

    def _bind_modal_keys(self, primary_btn: Optional[QPushButton], cancel_btn: Optional[QPushButton]):
        self._primary_btn = primary_btn
        self._cancel_btn = cancel_btn
        if primary_btn:
            primary_btn.setDefault(True)
            primary_btn.setAutoDefault(True)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self._primary_btn and self._primary_btn.isEnabled():
                self._primary_btn.click()
                event.accept()
                return
        elif key == Qt.Key_Escape:
            if self._cancel_btn and self._cancel_btn.isEnabled():
                self._cancel_btn.click()
                event.accept()
                return
            self.reject()
            event.accept()
            return
        super().keyPressEvent(event)


class DatePickDialog(BaseModalDialog):
    def __init__(self, parent: QWidget, title: str, label: str, allow_clear: bool = False):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat(DATE_FMT_QT)

        self._cleared = False

        form = QFormLayout()
        form.addRow(label, self.date_edit)

        self.inline_error = QLabel("")
        self.inline_error.setObjectName("errorText")

        btns = QHBoxLayout()
        okb = QPushButton("OK")
        cb = QPushButton("Cancelar")
        okb.clicked.connect(self.accept)
        cb.clicked.connect(self.reject)

        if allow_clear:
            clearb = QPushButton("Limpar")

            def _do_clear():
                self._cleared = True
                self.accept()

            clearb.clicked.connect(_do_clear)
            btns.addWidget(clearb)

        btns.addStretch()
        btns.addWidget(okb)
        btns.addWidget(cb)

        root = QVBoxLayout()
        root.addLayout(form)
        root.addLayout(btns)
        self.setLayout(root)
        self._bind_modal_keys(okb, cb)

    def was_cleared(self) -> bool:
        return self._cleared

    def selected_date_str(self) -> str:
        return qdate_to_date(self.date_edit.date()).strftime("%d/%m/%Y")


class PrazoMultiDialog(BaseModalDialog):
    def __init__(self, parent: QWidget, current_prazo: str):
        super().__init__(parent)
        self.setWindowTitle("Editar Prazo")

        self.picker = QDateEdit(QDate.currentDate())
        self.picker.setCalendarPopup(True)
        self.picker.setDisplayFormat(DATE_FMT_QT)

        self.listw = QListWidget()

        try:
            norm = normalize_prazo_text(current_prazo.replace("*", ""))
        except Exception:
            norm = ""
        if norm:
            for part in [p.strip() for p in norm.split(",") if p.strip()]:
                self.listw.addItem(part)

        addb = QPushButton("Adicionar")
        remb = QPushButton("Remover selecionada")
        addb.clicked.connect(self._add)
        remb.clicked.connect(self._remove)

        self.inline_error = QLabel("")
        self.inline_error.setObjectName("errorText")

        btns = QHBoxLayout()
        okb = QPushButton("OK")
        cb = QPushButton("Cancelar")
        okb.clicked.connect(self.accept)
        cb.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(okb)
        btns.addWidget(cb)

        top = QHBoxLayout()
        top.addWidget(self.picker)
        top.addWidget(addb)
        top.addWidget(remb)

        root = QVBoxLayout()
        root.addLayout(top)
        root.addWidget(self.listw)
        root.addLayout(btns)
        self.setLayout(root)
        self._bind_modal_keys(okb, cb)

    def _add(self):
        txt = self.picker.date().toString(DATE_FMT_QT)
        for i in range(self.listw.count()):
            if self.listw.item(i).text() == txt:
                return
        self.listw.addItem(txt)

    def _remove(self):
        for it in self.listw.selectedItems():
            self.listw.takeItem(self.listw.row(it))

    def prazo_str(self) -> str:
        prazos = ", ".join(self.listw.item(i).text() for i in range(self.listw.count()))
        return normalize_prazo_text(prazos)


class DeleteDemandDialog(BaseModalDialog):
    """
    Exclusão por ID (único ou múltiplos):
    - usuário informa IDs e app carrega as demandas
    - permite preload de seleção múltipla da tabela
    - bloqueia exclusão de demandas concluídas
    """
    def __init__(self, parent: QWidget, store: CsvStore):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Excluir demanda")

        self.line_input = QLineEdit()
        self.line_input.setPlaceholderText("Ex: 12 ou 1,3,5")

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)

        self.load_btn = QPushButton("Carregar")
        self.load_btn.clicked.connect(self._load_line)

        self.delete_btn = QPushButton("Excluir")
        self.cancel_btn = QPushButton("Cancelar")
        self.delete_btn.clicked.connect(self._do_delete)
        self.cancel_btn.clicked.connect(self._cancel_delete_action)

        self.delete_btn.setEnabled(False)
        self._loaded_rows: List[Dict[str, Any]] = []

        form = QFormLayout()
        form.addRow("Número(s) do ID*", self.line_input)

        top = QHBoxLayout()
        top.addWidget(self.load_btn)
        top.addStretch()

        self.inline_error = QLabel("")
        self.inline_error.setObjectName("errorText")

        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(self.delete_btn)
        btns.addWidget(self.cancel_btn)

        root = QVBoxLayout()
        root.addLayout(form)
        root.addLayout(top)
        root.addWidget(self.info_label)
        root.addLayout(btns)
        self.setLayout(root)
        self._bind_modal_keys(self.delete_btn, self.cancel_btn)

        self.reset_state()

    def reset_state(self):
        self._set_loaded_rows([])
        self.line_input.clear()
        self.line_input.setEnabled(True)
        self.load_btn.setEnabled(True)

    def _parse_input_lines(self, raw: str) -> List[int]:
        parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
        lines: List[int] = []
        for part in parts:
            if not part.isdigit():
                raise ValueError("Informe apenas números de ID separados por vírgula.")
            line = int(part)
            if line < 1:
                raise ValueError("Os IDs devem ser maiores que zero.")
            if line not in lines:
                lines.append(line)
        if not lines:
            raise ValueError("Informe ao menos um número de ID.")
        return lines

    def _format_row_info(self, row: Dict[str, Any]) -> str:
        return (
            f"ID {row.get('ID', '')}\n"
            f"Projeto: {row.get('Projeto', '')}\n"
            f"Prazo: {row.get('Prazo', '')}\n"
            f"Descrição: {row.get('Descrição', '')}\n"
            f"Status: {row.get('Status', '')}"
        )

    def _set_loaded_rows(self, rows: List[Dict[str, Any]]):
        self._loaded_rows = rows
        if not rows:
            self.info_label.setText("")
            self.delete_btn.setEnabled(False)
            return

        sections = [self._format_row_info(row) for row in rows]
        self.info_label.setText("\n\n--------------------\n\n".join(sections))

        has_concluded = any((row.get("Status") or "").strip() == "Concluído" for row in rows)
        if has_concluded:
            self.delete_btn.setEnabled(False)
            QMessageBox.warning(self, "Bloqueado", "Demandas concluídas não podem ser excluídas.")
        else:
            self.delete_btn.setEnabled(True)

    def _load_line(self):
        raw = (self.line_input.text() or "").strip()
        try:
            lines = self._parse_input_lines(raw)
        except ValueError as exc:
            QMessageBox.warning(self, "Inválido", str(exc))
            self._set_loaded_rows([])
            return

        self.store.load()
        view = self.store.build_view()

        rows: List[Dict[str, Any]] = []
        for line in lines:
            if line > len(view):
                QMessageBox.warning(self, "Não encontrado", f"Nenhuma demanda encontrada no ID {line}.")
                self._set_loaded_rows([])
                return
            rows.append(view[line - 1])

        self._set_loaded_rows(rows)

    def _do_delete(self):
        if not self._loaded_rows:
            return

        self.store.load()

        for row in self._loaded_rows:
            _id = row.get("_id")
            if not _id:
                QMessageBox.warning(self, "Falha", "Demanda inválida para exclusão.")
                self.reject()
                return

            dr = self.store.get(_id)
            if dr and (dr.data.get("Status") or "").strip() == "Concluído":
                QMessageBox.warning(self, "Bloqueado", "Demandas concluídas não podem ser excluídas.")
                self.reject()
                return

        for row in self._loaded_rows:
            _id = row.get("_id")
            if not self.store.delete_by_id(_id):
                QMessageBox.warning(self, "Falha", "Não foi possível excluir uma das demandas selecionadas.")
                self.reject()
                return
        self.reset_state()
        self.accept()

    def _cancel_delete_action(self):
        self.reset_state()
        self.reject()

    def preload_selected(self, row_data: Dict[str, Any]):
        self.preload_selected_rows([row_data])

    def preload_selected_rows(self, rows_data: List[Dict[str, Any]]):
        self.reset_state()
        ids = [str(row.get("ID", "") or "") for row in rows_data if str(row.get("ID", "") or "").isdigit()]
        self.line_input.setText(", ".join(ids))
        self.line_input.setEnabled(False)
        self.load_btn.setEnabled(False)

        self._set_loaded_rows(rows_data)


class DeleteTeamMembersDialog(BaseModalDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Excluir funcionário")

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.confirm_btn = QPushButton("Confirmar")
        self.cancel_btn = QPushButton("Cancelar")

        self.confirm_btn.clicked.connect(self._confirm_delete_action)
        self.cancel_btn.clicked.connect(self._cancel_delete_action)

        self._selected_members: List[Tuple[str, str]] = []

        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(self.confirm_btn)
        btns.addWidget(self.cancel_btn)

        root = QVBoxLayout()
        root.addWidget(QLabel("Atenção: Funcionário será excluído permanentemente do controle"))
        root.addWidget(self.info_label)
        root.addLayout(btns)
        self.setLayout(root)
        self._bind_modal_keys(self.confirm_btn, self.cancel_btn)

        self.reset_state()

    def reset_state(self):
        self._selected_members = []
        self.info_label.setText("")
        self.confirm_btn.setEnabled(False)

    def preload_members(self, members: List[Tuple[str, str]]):
        self.reset_state()
        unique_members: List[Tuple[str, str]] = []
        seen_member_ids = set()
        for member_id, member_name in members:
            if not member_id or member_id in seen_member_ids:
                continue
            unique_members.append((member_id, member_name))
            seen_member_ids.add(member_id)

        self._selected_members = unique_members
        names_text = "\n".join(f"- {member_name}" for _, member_name in unique_members)
        self.info_label.setText(f"Nome(s):\n{names_text}" if names_text else "")
        self.confirm_btn.setEnabled(bool(unique_members))

    def selected_member_ids(self) -> List[str]:
        return [member_id for member_id, _ in self._selected_members]

    def _confirm_delete_action(self):
        self.accept()

    def _cancel_delete_action(self):
        self.reset_state()
        self.reject()

    def reject(self):
        self.reset_state()
        super().reject()


class NewDemandDialog(BaseModalDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Nova demanda")

        self.status = QComboBox()
        self.status.setEditable(False)
        self.status.addItems(STATUS_EDIT_OPTIONS)

        self.prioridade = QComboBox()
        self.prioridade.setEditable(False)
        self.prioridade.addItem("")
        self.prioridade.addItems(PRIORIDADE_EDIT_OPTIONS)

        self.data_registro = QDateEdit(QDate.currentDate())
        self.data_registro.setCalendarPopup(True)
        self.data_registro.setDisplayFormat(DATE_FMT_QT)

        self.responsavel = QLineEdit()
        self.responsavel.setPlaceholderText("Ex: Ana Silva")
        self.descricao = QTextEdit()
        self.descricao.setPlaceholderText("Descreva a demanda com contexto e resultado esperado")

        self.urgente = QComboBox()
        self.urgente.setEditable(False)
        self.urgente.addItem("")
        self.urgente.addItems(URGENCIA_EDIT_OPTIONS)

        self.projeto = QLineEdit()
        self.projeto.setPlaceholderText("Ex: Migração ERP")
        self.id_azure = QLineEdit()
        self.id_azure.setPlaceholderText("Ex: AB#12345")

        self.perc = QComboBox()
        self.perc.setEditable(False)
        for label, _val in PERCENT_OPTIONS:
            self.perc.addItem(label)

        self.reportar = QComboBox()
        self.reportar.setEditable(False)
        self.reportar.addItem("")
        self.reportar.addItems(REPORTAR_EDIT_OPTIONS)

        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Nome de referência")
        self.time_funcao = QLineEdit()
        self.time_funcao.setPlaceholderText("Ex: Engenharia de Dados")

        self._conclusao_txt: str = ""
        self.conclusao_value = QLabel("")
        self.conclusao_value.setStyleSheet("padding: 4px; border: 1px solid #ccc;")

        sel_conc = QPushButton("Selecionar")
        clr_conc = QPushButton("Limpar")
        sel_conc.clicked.connect(self._select_conclusao)
        clr_conc.clicked.connect(self._clear_conclusao)

        conc_row = QHBoxLayout()
        conc_row.addWidget(self.conclusao_value, 1)
        conc_row.addWidget(sel_conc)
        conc_row.addWidget(clr_conc)

        self.prazo_label = QLabel("Prazo* (É possível informar mais de uma data)")
        self.prazo_picker = QDateEdit(QDate.currentDate())
        self.prazo_picker.setCalendarPopup(True)
        self.prazo_picker.setDisplayFormat(DATE_FMT_QT)
        self.prazo_list = QListWidget()

        add_prazo = QPushButton("Adicionar data")
        rem_prazo = QPushButton("Remover selecionada")
        add_prazo.clicked.connect(self._add_prazo)
        rem_prazo.clicked.connect(self._remove_prazo)

        prazo_box = QVBoxLayout()
        prazo_box.addWidget(self.prazo_label)
        line = QHBoxLayout()
        line.addWidget(self.prazo_picker)
        line.addWidget(add_prazo)
        prazo_box.addLayout(line)
        prazo_box.addWidget(self.prazo_list)
        prazo_box.addWidget(rem_prazo)

        self.inline_error = QLabel("")
        self.inline_error.setObjectName("errorText")

        btns = QHBoxLayout()
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)

        obrig_box = QGroupBox("Campos obrigatórios")
        obrig_form = QFormLayout()
        obrig_form.addRow("Status*", self.status)
        obrig_form.addRow("Prioridade*", self.prioridade)
        obrig_form.addRow("Data de Registro*", self.data_registro)
        obrig_form.addRow("Responsável*", self.responsavel)
        obrig_form.addRow("Descrição*", self.descricao)
        obrig_box.setLayout(obrig_form)

        opc_box = QGroupBox("Controle e identificação")
        opc_form = QFormLayout()
        opc_form.addRow("É Urgente?", self.urgente)
        opc_form.addRow("Projeto", self.projeto)
        opc_form.addRow("ID Azure", self.id_azure)
        opc_form.addRow("% Conclusão", self.perc)
        opc_form.addRow("Data Conclusão", conc_row)
        opc_form.addRow("Reportar?", self.reportar)
        opc_form.addRow("Nome", self.nome)
        opc_form.addRow("Time/Função", self.time_funcao)
        opc_box.setLayout(opc_form)

        prazo_group = QGroupBox("Planejamento de prazo")
        prazo_group.setLayout(prazo_box)

        root = QVBoxLayout()
        root.addWidget(obrig_box)
        root.addWidget(opc_box)
        root.addWidget(prazo_group)
        root.addWidget(self.inline_error)
        root.addLayout(btns)
        self.setLayout(root)
        self._bind_modal_keys(save_btn, cancel_btn)

    def _select_conclusao(self):
        dlg = DatePickDialog(self, "Data Conclusão", "Selecione a data de conclusão:", allow_clear=False)
        if dlg.exec() == QDialog.Accepted:
            self._conclusao_txt = dlg.selected_date_str()
            self.conclusao_value.setText(self._conclusao_txt)
            # regra: data conclusão => concluído + 100%
            self.status.setCurrentText("Concluído")
            self.perc.setCurrentText("100% - Concluído")

    def _clear_conclusao(self):
        self._conclusao_txt = ""
        self.conclusao_value.setText("")

    def _add_prazo(self):
        txt = self.prazo_picker.date().toString(DATE_FMT_QT)
        for i in range(self.prazo_list.count()):
            if self.prazo_list.item(i).text() == txt:
                return
        self.prazo_list.addItem(txt)

    def _remove_prazo(self):
        for it in self.prazo_list.selectedItems():
            self.prazo_list.takeItem(self.prazo_list.row(it))

    def _on_save(self):
        payload = {
            "Descrição": self.descricao.toPlainText(),
            "Prioridade": self.prioridade.currentText(),
            "Status": self.status.currentText(),
            "Responsável": self.responsavel.text(),
            "% Conclusão": self.perc.currentText(),
            "Data Conclusão": self._conclusao_txt,
        }
        missing = required_fields(payload, self.prazo_list.count())

        self.inline_error.setText("")
        self.responsavel.setStyleSheet("")
        self.descricao.setStyleSheet("")
        self.prioridade.setStyleSheet("")
        self.status.setStyleSheet("")
        self.conclusao_value.setStyleSheet("padding: 4px; border: 1px solid #ccc;")

        if "Responsável" in missing:
            self.responsavel.setStyleSheet("border: 1px solid #d92d20;")
        if "Descrição" in missing:
            self.descricao.setStyleSheet("border: 1px solid #d92d20;")
        if "Prioridade" in missing:
            self.prioridade.setStyleSheet("border: 1px solid #d92d20;")
        if "Status" in missing:
            self.status.setStyleSheet("border: 1px solid #d92d20;")
        if "Data Conclusão" in missing:
            self.conclusao_value.setStyleSheet("padding: 4px; border: 1px solid #d92d20;")

        if missing:
            friendly = [m if m != "Prazo" else "Prazo (adicione ao menos uma data)" for m in missing]
            self.inline_error.setText("Preencha os campos: " + ", ".join(friendly))
            return

        self.accept()

    def payload(self) -> Dict[str, str]:
        prazos = ", ".join(self.prazo_list.item(i).text() for i in range(self.prazo_list.count()))
        prazos = normalize_prazo_text(prazos)

        selected_label = self.perc.currentText()
        percent_value = ""
        for label, val in PERCENT_OPTIONS:
            if label == selected_label:
                percent_value = val
                break

        payload = {
            "É Urgente?": self.urgente.currentText(),
            "Status": self.status.currentText(),
            "Prioridade": self.prioridade.currentText(),
            "Data de Registro": qdate_to_date(self.data_registro.date()).strftime("%d/%m/%Y"),
            "Prazo": prazos,
            "Data Conclusão": self._conclusao_txt,
            "Projeto": self.projeto.text(),
            "Descrição": self.descricao.toPlainText(),
            "ID Azure": self.id_azure.text(),
            "% Conclusão": percent_value,
            "Responsável": self.responsavel.text(),
            "Reportar?": self.reportar.currentText(),
            "Nome": self.nome.text(),
            "Time/Função": self.time_funcao.text(),
        }

        return validate_payload(payload, mode="create")


class AddTeamMemberDialog(BaseModalDialog):
    def __init__(self, parent: QWidget, team_names: List[str]):
        super().__init__(parent)
        self.setWindowTitle("Adicionar funcionário")

        self.name_input = QPlainTextEdit()
        self.name_input.setPlaceholderText("Digite um ou vários nomes (separe por vírgula ou quebra de linha)")
        self.name_input.setFixedHeight(120)

        self.team_combo = QComboBox()
        self.team_combo.addItems(team_names)
        self.team_combo.addItem("+ Novo time")

        self.new_team_label = QLabel("Novo Time")
        self.new_team_input = QLineEdit()
        self.new_team_input.setPlaceholderText("Nome do novo time")
        self.new_team_label.setVisible(False)
        self.new_team_input.setVisible(False)

        self.inline_error = QLabel("")
        self.inline_error.setStyleSheet("color: #d92d20;")

        self.team_combo.currentTextChanged.connect(self._on_team_change)

        form = QFormLayout()
        form.addRow("Nome(s)*", self.name_input)
        form.addRow("Time", self.team_combo)
        form.addRow(self.new_team_label, self.new_team_input)

        actions = QHBoxLayout()
        ok = QPushButton("Adicionar")
        cancel = QPushButton("Cancelar")
        ok.clicked.connect(self._submit)
        cancel.clicked.connect(self.reject)
        actions.addStretch()
        actions.addWidget(ok)
        actions.addWidget(cancel)

        self.new_team_input.returnPressed.connect(self._submit)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.inline_error)
        layout.addLayout(actions)
        self._bind_modal_keys(ok, cancel)

    def _on_team_change(self, text: str):
        is_new = text == "+ Novo time"
        self.new_team_label.setVisible(is_new)
        self.new_team_input.setVisible(is_new)

    def _submit(self):
        if not split_member_names(self.name_input.toPlainText()):
            self.inline_error.setText("Informe ao menos um nome.")
            return
        if self.team_combo.currentText() == "+ Novo time" and not self.new_team_input.text().strip():
            self.inline_error.setText("Informe o nome do novo time.")
            return
        self.accept()

    def payload(self) -> Dict[str, str]:
        return {
            "names": self.name_input.toPlainText().strip(),
            "team_name": self.team_combo.currentText(),
            "new_team_name": self.new_team_input.text().strip(),
        }


class CopyTeamMembersDialog(BaseModalDialog):
    def __init__(self, parent: QWidget, team_store: TeamControlStore, selected_names: List[str], default_year: int, default_month: int):
        super().__init__(parent)
        self.setWindowTitle("Copiar Nome(s)")
        self.team_store = team_store
        self.selected_names = selected_names

        self.year_combo = QComboBox()
        current_year = date.today().year
        for y in range(current_year - 2, current_year + 6):
            self.year_combo.addItem(str(y))
        self.year_combo.setCurrentText(str(default_year))

        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(f"{m:02d}")
        self.month_combo.setCurrentText(f"{default_month:02d}")

        self.team_combo = QComboBox()

        self.inline_error = QLabel("")
        self.inline_error.setStyleSheet("color: #d92d20;")

        self.year_combo.currentTextChanged.connect(self._refresh_teams)
        self.month_combo.currentTextChanged.connect(self._refresh_teams)

        form = QFormLayout()
        form.addRow("Nome(s)", QLabel(", ".join(selected_names)))
        form.addRow("Ano", self.year_combo)
        form.addRow("Mês", self.month_combo)
        form.addRow("Time", self.team_combo)

        actions = QHBoxLayout()
        ok = QPushButton("Copiar")
        cancel = QPushButton("Cancelar")
        ok.clicked.connect(self._submit)
        cancel.clicked.connect(self.reject)
        actions.addStretch()
        actions.addWidget(ok)
        actions.addWidget(cancel)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.inline_error)
        layout.addLayout(actions)
        self._bind_modal_keys(ok, cancel)

        self._refresh_teams()

    def _refresh_teams(self):
        year = int(self.year_combo.currentText())
        month = int(self.month_combo.currentText())
        sections = self.team_store.get_sections_for_period(year, month)

        self.team_combo.clear()
        for section in sections:
            self.team_combo.addItem(section.name, section.id)

        has_teams = bool(sections)
        self.team_combo.setEnabled(has_teams)
        if not has_teams:
            self.inline_error.setText("Crie o time desejado no ano e mês selecionado antes de copiar os nomes desejados")
        else:
            self.inline_error.setText("")

    def _submit(self):
        if self.team_combo.count() == 0:
            self.inline_error.setText("Crie o time desejado no ano e mês selecionado antes de copiar os nomes desejados")
            return
        self.accept()

    def payload(self) -> Dict[str, str]:
        return {
            "year": self.year_combo.currentText(),
            "month": self.month_combo.currentText(),
            "section_id": str(self.team_combo.currentData() or ""),
            "section_name": self.team_combo.currentText(),
        }


class MainWindow(QMainWindow):
    def __init__(self, store: CsvStore):
        super().__init__()
        self.store = store
        self.setWindowTitle("DemandasApp")
        icon_path = _app_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._filling = False

        self.tabs = QTabWidget()
        self.tabs.setMovable(True)
        self.tabs.tabBar().tabMoved.connect(self._save_preferences)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(8, 8, 8, 8)
        central_layout.setSpacing(8)
        central_layout.addWidget(self._build_shortcuts_section())
        central_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        self._prefs = load_prefs(self.store.base_dir)
        self.team_store = TeamControlStore(self.store.base_dir)

        self._init_tab1()
        self._init_tab2()
        self._init_tab3()
        self._init_tab4()

        self.refresh_all()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._restore_preferences()

    def _make_table(self) -> QTableWidget:
        table = QTableWidget(0, len(VISIBLE_COLUMNS))
        table.setHorizontalHeaderLabels(VISIBLE_COLUMNS)
        table.itemChanged.connect(self._on_item_changed)
        table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        col_map = {}
        col_map[VISIBLE_COLUMNS.index("Status")] = STATUS_EDIT_OPTIONS
        col_map[VISIBLE_COLUMNS.index("Prioridade")] = PRIORIDADE_EDIT_OPTIONS
        col_map[VISIBLE_COLUMNS.index("É Urgente?")] = URGENCIA_EDIT_OPTIONS
        col_map[VISIBLE_COLUMNS.index("Reportar?")] = REPORTAR_EDIT_OPTIONS
        # ✅ % Conclusão vira combo
        col_map[VISIBLE_COLUMNS.index("% Conclusão")] = PERCENT_COMBO_OPTIONS

        table.setItemDelegate(ColumnComboDelegate(table, col_map))
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        table.verticalHeader().setVisible(False)
        table.setWordWrap(True)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        desc_col = VISIBLE_COLUMNS.index("Descrição")
        desc_width = table.fontMetrics().horizontalAdvance("M" * DESC_COLUMN_MAX_CHARS)
        header.setSectionResizeMode(desc_col, QHeaderView.Interactive)
        table.setColumnWidth(desc_col, desc_width)

        return table

    def _set_item(self, table: QTableWidget, r: int, c: int, text: str, _id: str):
        it = QTableWidgetItem(text or "")
        colname = VISIBLE_COLUMNS[c]

        if colname == "Descrição":
            it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        else:
            it.setTextAlignment(Qt.AlignCenter)

        if colname in NON_EDITABLE:
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)

        it.setData(Qt.UserRole, _id)

        # guarda valor anterior do status
        if colname == "Status":
            it.setData(Qt.UserRole + 1, text or "")

        if colname == "Status":
            rr, gg, bb = status_color(text)
            it.setBackground(QColor(rr, gg, bb))
        if colname == "Prioridade":
            color = PRIORIDADE_TEXT_COLORS.get((text or "").strip().lower())
            if color:
                rr, gg, bb = color
                it.setForeground(QColor(rr, gg, bb))
        if colname == "Timing":
            rr, gg, bb = timing_color(text)
            it.setBackground(QColor(rr, gg, bb))
        if colname == "Prazo" and prazo_contains_today(text):
            rr, gg, bb = PRAZO_TODAY_BG
            it.setBackground(QColor(rr, gg, bb))
        if colname == "% Conclusão":
            fraction = _percent_to_fraction(text)
            if fraction and fraction > 0:
                rr, gg, bb = PROGRESS_FILL_COLOR
                grad = QLinearGradient(0, 0, 1, 0)
                grad.setCoordinateMode(QGradient.ObjectBoundingMode)
                grad.setColorAt(0.0, QColor(rr, gg, bb))
                grad.setColorAt(fraction, QColor(rr, gg, bb))
                # mantém o restante da célula sem preenchimento.
                grad.setColorAt(min(fraction + 0.001, 1.0), QColor(0, 0, 0, 0))
                grad.setColorAt(1.0, QColor(0, 0, 0, 0))
                it.setBackground(QBrush(grad))

        table.setItem(r, c, it)

    def _fill(self, table: QTableWidget, rows: List[Dict[str, Any]]):
        self._filling = True
        try:
            table.setRowCount(0)
            for row in rows:
                r = table.rowCount()
                table.insertRow(r)
                _id = row["_id"]
                for c, col in enumerate(VISIBLE_COLUMNS):
                    self._set_item(table, r, c, str(row.get(col, "") or ""), _id)
        finally:
            self._filling = False

        table.resizeRowsToContents()

    def _prompt_conclusao_date_required(self) -> Optional[str]:
        dlg = DatePickDialog(self, "Data de Conclusão", "Selecione a data de conclusão:", allow_clear=False)
        if dlg.exec() == QDialog.Accepted:
            return dlg.selected_date_str()
        return None

    def _prompt_percent_when_unconcluding(self) -> Optional[str]:
        items = [lbl for (lbl, _v) in PERCENT_QUICK_PICK]
        choice, ok = QInputDialog.getItem(
            self,
            "% Conclusão",
            "Informe o % conclusão para este novo status:",
            items,
            0,
            False
        )
        if not ok:
            return None
        mapping = {lbl: v for (lbl, v) in PERCENT_QUICK_PICK}
        return mapping.get(choice, "")

    def _on_cell_double_clicked(self, row: int, col: int):
        col_name = VISIBLE_COLUMNS[col]
        table = self.sender()
        if not isinstance(table, QTableWidget):
            return

        it = table.item(row, col)
        if not it:
            return
        _id = it.data(Qt.UserRole)
        if not _id:
            return

        # Data de Registro / Data Conclusão (picker)
        if col_name in ("Data de Registro", "Data Conclusão"):
            allow_clear = (col_name == "Data Conclusão")
            dlg = DatePickDialog(self, col_name, f"Selecione {col_name.lower()}:", allow_clear=allow_clear)
            if dlg.exec() != QDialog.Accepted:
                return

            if allow_clear and dlg.was_cleared():
                # limpar data conclusão (mantém suas regras: status não muda aqui)
                try:
                    self.store.update(_id, {col_name: ""})
                except ValidationError as ve:
                    QMessageBox.warning(self, "Validação", str(ve))
                self.refresh_all()
                return

            selected = dlg.selected_date_str()

            if col_name == "Data Conclusão":
                # ✅ data conclusão => status concluído + % 100
                try:
                    self.store.update(_id, {"Data Conclusão": selected, "Status": "Concluído", "% Conclusão": "1"})
                except ValidationError as ve:
                    QMessageBox.warning(self, "Validação", str(ve))
                self.refresh_all()
                return

            try:
                self.store.update(_id, {col_name: selected})
            except ValidationError as ve:
                QMessageBox.warning(self, "Validação", str(ve))
            self.refresh_all()
            return

        # Prazo (multi datas)
        if col_name == "Prazo":
            current = (it.text() or "").replace("*", "")
            dlg = PrazoMultiDialog(self, current)
            if dlg.exec() != QDialog.Accepted:
                return
            try:
                self.store.update(_id, {"Prazo": dlg.prazo_str()})
            except ValidationError as ve:
                QMessageBox.warning(self, "Validação", str(ve))
            self.refresh_all()
            return

    def _on_item_changed(self, item: QTableWidgetItem):
        if self._filling:
            return

        _id = item.data(Qt.UserRole)
        if not _id:
            return

        col_name = VISIBLE_COLUMNS[item.column()]
        if col_name in NON_EDITABLE:
            return

        new_value = (item.text() or "").strip()

        # Status -> Concluído: exige data conclusão e força % 100
        if col_name == "Status" and new_value == "Concluído":
            concl = self._prompt_conclusao_date_required()
            if not concl:
                self.refresh_all()
                return
            try:
                self.store.update(_id, {"Status": "Concluído", "Data Conclusão": concl, "% Conclusão": "1"})
            except ValidationError as ve:
                QMessageBox.warning(self, "Validação", str(ve))
            self.refresh_all()
            return

        # Status: Concluído -> outro (pede % e limpa data conclusão)
        if col_name == "Status":
            old_value = (item.data(Qt.UserRole + 1) or "").strip()
            if old_value == "Concluído" and new_value != "Concluído":
                pct = self._prompt_percent_when_unconcluding()
                if pct is None:
                    self.refresh_all()
                    return
                try:
                    self.store.update(_id, {"Status": new_value, "% Conclusão": pct, "Data Conclusão": ""})
                except ValidationError as ve:
                    QMessageBox.warning(self, "Validação", str(ve))
                self.refresh_all()
                return

        # ✅ % Conclusão via combo
        if col_name == "% Conclusão":
            # new_value é tipo "25%" etc
            pct_dec = _normalize_percent_to_decimal_str(new_value)
            if _is_percent_100(new_value):
                concl = self._prompt_conclusao_date_required()
                if not concl:
                    self.refresh_all()
                    return
                try:
                    self.store.update(_id, {"% Conclusão": "1", "Status": "Concluído", "Data Conclusão": concl})
                except ValidationError as ve:
                    QMessageBox.warning(self, "Validação", str(ve))
                self.refresh_all()
                return

            try:
                self.store.update(_id, {"% Conclusão": pct_dec})
            except ValidationError as ve:
                QMessageBox.warning(self, "Validação", str(ve))
            self.refresh_all()
            return

        # default: salva campo normal
        try:
            self.store.update(_id, {col_name: new_value})
        except ValidationError as ve:
            QMessageBox.warning(self, "Validação", str(ve))
        except Exception as e:
            debug_msg("Erro ao salvar", str(e))
        self.refresh_all()

    def _restore_preferences(self):
        idx = int(self._prefs.get("tab_index", 0) or 0)
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)
        self.t3_search.setText(str(self._prefs.get("t3_search", "") or ""))
        self.t3_status.setCurrentText(str(self._prefs.get("t3_status", "") or ""))
        self.t3_prioridade.setCurrentText(str(self._prefs.get("t3_prioridade", "") or ""))
        self.t3_responsavel.setText(str(self._prefs.get("t3_responsavel", "") or ""))

        tab_order = self._prefs.get("tab_order")
        if isinstance(tab_order, list):
            self._restore_tab_order(tab_order)

    def _save_preferences(self):
        data = {
            "tab_index": self.tabs.currentIndex(),
            "t3_search": self.t3_search.text(),
            "t3_status": self.t3_status.currentText(),
            "t3_prioridade": self.t3_prioridade.currentText(),
            "t3_responsavel": self.t3_responsavel.text(),
            "tab_order": [self.tabs.tabText(i) for i in range(self.tabs.count())],
        }
        save_prefs(self.store.base_dir, data)

    def _restore_tab_order(self, tab_order: List[str]):
        for target_idx, title in enumerate(tab_order):
            current_idx = next((i for i in range(self.tabs.count()) if self.tabs.tabText(i) == title), -1)
            if current_idx >= 0 and current_idx != target_idx:
                self.tabs.tabBar().moveTab(current_idx, target_idx)

    def _on_tab_changed(self, idx: int):
        self._save_preferences()
        self.refresh_current()

    def _build_toolbar_action_button(self, object_name: str, tooltip: str, img_name: str, fallback_icon: QStyle.StandardPixmap, on_click) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName(object_name)
        btn.setProperty("toolbarAction", True)
        btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        btn.setToolTip(tooltip)
        btn.setIcon(self._icon_from_img(img_name, fallback_icon))
        btn.setIconSize(QSize(28, 28))
        btn.clicked.connect(on_click)
        return btn

    def _icon_from_img(self, img_name: str, fallback_icon: QStyle.StandardPixmap) -> QIcon:
        img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", img_name)
        if img_name and os.path.exists(img_path):
            return QIcon(img_path)
        return self.style().standardIcon(fallback_icon)

    def _build_shortcuts_section(self) -> QWidget:
        section = QWidget()
        layout = QHBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        new_btn = self._build_toolbar_action_button(
            object_name="primaryAction",
            tooltip="Adicionar demandas",
            img_name="add.png",
            fallback_icon=QStyle.SP_FileDialogNewFolder,
            on_click=self.new_demand,
        )

        delete_btn = self._build_toolbar_action_button(
            object_name="dangerAction",
            tooltip="Remover demandas",
            img_name="",
            fallback_icon=QStyle.SP_TrashIcon,
            on_click=self.delete_demand,
        )

        export_shortcut = self._build_toolbar_action_button(
            object_name="exportAction",
            tooltip="Exportar demandas",
            img_name="exp.png",
            fallback_icon=QStyle.SP_ArrowUp,
            on_click=self.export_demands_csv,
        )
        import_shortcut = self._build_toolbar_action_button(
            object_name="importAction",
            tooltip="Importar demandas",
            img_name="exp.png",
            fallback_icon=QStyle.SP_ArrowDown,
            on_click=self.import_demands_csv,
        )

        layout.addWidget(new_btn)
        layout.addWidget(delete_btn)
        layout.addWidget(export_shortcut)
        layout.addWidget(import_shortcut)
        layout.addStretch()
        return section

    def _init_tab2(self):
        tab = QWidget()

        self.tc_year = QComboBox()
        current_year = date.today().year
        for y in range(current_year - 2, current_year + 6):
            self.tc_year.addItem(str(y))
        self.tc_year.setCurrentText(str(current_year))

        self.tc_month = QComboBox()
        for m in range(1, 13):
            self.tc_month.addItem(f"{m:02d}")
        self.tc_month.setCurrentText(f"{date.today().month:02d}")
        self.tc_year.setMinimumContentsLength(5)
        self.tc_month.setMinimumContentsLength(4)
        self.tc_year.setMinimumWidth(int(self.tc_year.sizeHint().width() * 1.25))
        self.tc_month.setMinimumWidth(int(self.tc_month.sizeHint().width() * 1.25))

        refresh_btn = QPushButton("Atualizar")
        refresh_btn.clicked.connect(self.refresh_team_control)

        add_section_btn = QPushButton("Novo time")
        add_section_btn.clicked.connect(self._create_team_section)

        del_section_btn = QPushButton("Excluir time")
        del_section_btn.clicked.connect(self._delete_team_section)

        add_member_btn = QPushButton("Adicionar nome")
        add_member_btn.clicked.connect(self._open_add_team_member_dialog)

        export_team_btn = QPushButton("Baixar relatório")
        export_team_btn.clicked.connect(self.export_team_control_csv)

        top = QHBoxLayout()
        top.addWidget(QLabel("Ano:"))
        top.addWidget(self.tc_year)
        top.addWidget(QLabel("Mês:"))
        top.addWidget(self.tc_month)
        top.addWidget(refresh_btn)
        top.addSpacing(20)
        top.addWidget(add_section_btn)
        top.addWidget(del_section_btn)
        top.addWidget(add_member_btn)
        top.addWidget(export_team_btn)
        top.addStretch()

        self.tc_scroll = QScrollArea()
        self.tc_scroll.setWidgetResizable(True)
        self.tc_scroll_host = QWidget()
        self.tc_sections_layout = QVBoxLayout(self.tc_scroll_host)
        self.tc_sections_layout.setContentsMargins(0, 0, 0, 0)
        self.tc_sections_layout.setSpacing(14)
        self.tc_scroll.setWidget(self.tc_scroll_host)

        layout = QVBoxLayout()
        legend = QLabel("Use: P - Presente, A - Ausente, K - Com demanda, F - Férias, D - Day-off, H - Feriado e R - Recesso")
        layout.addLayout(top)
        layout.addWidget(legend)
        layout.addWidget(self.tc_scroll)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Presenças do Time")

    def _selected_year_month(self) -> tuple[int, int]:
        return int(self.tc_year.currentText()), int(self.tc_month.currentText())

    def _clear_layout(self, layout: QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget:
                widget.deleteLater()
            if child_layout:
                self._clear_layout(child_layout)

    def refresh_team_control(self):
        year, month = self._selected_year_month()
        self.team_store.load()
        self.team_store.set_period(year, month)
        self._clear_layout(self.tc_sections_layout)
        if not self.team_store.sections:
            self.tc_sections_layout.addWidget(QLabel("Nenhum time criado. Clique em 'Novo time'."))
            self.tc_sections_layout.addStretch()
            return

        total_days = month_days(year, month)
        today = date.today()

        for section in self.team_store.sections:
            box = QGroupBox(section.name)
            box_layout = QVBoxLayout(box)

            table = TeamSectionTable()
            table.setColumnCount(total_days + 2)
            table.setObjectName(f"teamSectionTable::{section.id}")
            table.setProperty("sectionId", section.id)
            table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed | QAbstractItemView.AnyKeyPressed)
            table.setSelectionBehavior(QAbstractItemView.SelectItems)
            table.setSelectionMode(QAbstractItemView.ExtendedSelection)
            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.set_bulk_edit_handler(self._bulk_fill_team_cells)
            table.customContextMenuRequested.connect(self._open_member_context_menu)
            table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
            table.horizontalHeader().setMinimumSectionSize(48)
            table.horizontalHeader().setFixedHeight(42)
            table.verticalHeader().setVisible(False)

            month_part_col = total_days + 1
            headers_top = [section.name]
            headers_bottom = ["Nomes"]
            for d in range(1, total_days + 1):
                curr = date(year, month, d)
                headers_top.append(WEEKDAY_LABELS[curr.weekday()])
                headers_bottom.append(curr.strftime("%d/%m"))
            headers_top.append("Participação")
            headers_bottom.append("Mês")
            table.setHorizontalHeaderLabels(headers_bottom)

            for c, text in enumerate(headers_top):
                item = table.horizontalHeaderItem(c)
                if not item:
                    item = QTableWidgetItem()
                    table.setHorizontalHeaderItem(c, item)
                item.setText(f"{text}\n{headers_bottom[c] if c > 0 else ""}".strip())
                curr_date = date(year, month, c) if 0 < c <= total_days else None
                curr_is_today = curr_date == today
                if curr_is_today:
                    item.setBackground(QColor(220, 38, 38))
                    item.setForeground(QColor(0, 0, 0))
                elif curr_date and curr_date.weekday() >= 5:
                    item.setBackground(QColor(229, 231, 235))

            table.setColumnWidth(0, 170)
            for d in range(1, total_days + 1):
                table.setColumnWidth(d, 52)
            table.setColumnWidth(month_part_col, 90)

            weekend_bg = QColor(229, 231, 235)
            month_participation_bg = QColor(229, 231, 235)

            for member in section.members:
                r = table.rowCount()
                table.insertRow(r)
                name_item = QTableWidgetItem(member.name)
                name_item.setData(Qt.UserRole, member.id)
                table.setItem(r, 0, name_item)
                for d in range(1, total_days + 1):
                    curr = date(year, month, d)
                    key = curr.isoformat()
                    value = member.entries.get(key, "")
                    it = QTableWidgetItem(value)
                    it.setTextAlignment(Qt.AlignCenter)
                    if value in STATUS_COLORS:
                        br, bg, bb, fr, fg, fb = STATUS_COLORS[value]
                        it.setBackground(QColor(br, bg, bb))
                        it.setForeground(QColor(fr, fg, fb))
                    elif curr.weekday() >= 5:
                        it.setBackground(weekend_bg)
                    table.setItem(r, d, it)

                month_total = QTableWidgetItem(str(monthly_k_count(member, year, month)))
                month_total.setTextAlignment(Qt.AlignCenter)
                month_total.setFlags(month_total.flags() & ~Qt.ItemIsEditable)
                month_total.setBackground(month_participation_bg)
                month_total.setForeground(QColor(0, 0, 0))
                table.setItem(r, month_part_col, month_total)

            footer_row = table.rowCount()
            table.insertRow(footer_row)
            part = QTableWidgetItem("Participação Dia")
            part.setFlags(part.flags() & ~Qt.ItemIsEditable)
            part.setTextAlignment(Qt.AlignCenter)
            part.setBackground(QColor(255, 255, 255))
            table.setItem(footer_row, 0, part)
            for d in range(1, total_days + 1):
                curr = date(year, month, d)
                col_entries = []
                for member in section.members:
                    col_entries.append(member.entries.get(curr.isoformat(), ""))
                total = participation_for_date(col_entries)
                text = str(total) if total > 0 else ""
                pit = QTableWidgetItem(text)
                pit.setTextAlignment(Qt.AlignCenter)
                pit.setFlags(pit.flags() & ~Qt.ItemIsEditable)
                pit.setBackground(QColor(255, 255, 255) if text else weekend_bg)
                table.setItem(footer_row, d, pit)

            footer_month = QTableWidgetItem("")
            footer_month.setTextAlignment(Qt.AlignCenter)
            footer_month.setFlags(footer_month.flags() & ~Qt.ItemIsEditable)
            footer_month.setBackground(month_participation_bg)
            footer_month.setForeground(QColor(0, 0, 0))
            table.setItem(footer_row, month_part_col, footer_month)

            table.fit_height_to_rows()

            table.itemChanged.connect(self._on_team_table_item_changed)
            box_layout.addWidget(table)
            self.tc_sections_layout.addWidget(box)

        self.tc_sections_layout.addStretch()

    def _create_team_section(self):
        year, month = self._selected_year_month()
        self.team_store.set_period(year, month)
        name, ok = QInputDialog.getText(self, "Novo time", "Nome do time:")
        if not ok:
            return
        try:
            self.team_store.create_section(name)
        except ValueError as e:
            QMessageBox.warning(self, "Time", str(e))
            return
        self.refresh_team_control()

    def _delete_team_section(self):
        year, month = self._selected_year_month()
        self.team_store.set_period(year, month)
        names = [s.name for s in self.team_store.sections]
        if not names:
            QMessageBox.information(self, "Times", "Não há times para excluir.")
            return
        chosen, ok = QInputDialog.getItem(self, "Excluir time", "Selecione o time:", names, 0, False)
        if not ok:
            return
        section = next((s for s in self.team_store.sections if s.name == chosen), None)
        if not section:
            return
        confirm = QMessageBox.question(self, "Excluir time", f"Deseja excluir o time '{section.name}'?")
        if confirm != QMessageBox.Yes:
            return
        self.team_store.delete_section(section.id)
        self.refresh_team_control()

    def _open_add_team_member_dialog(self):
        year, month = self._selected_year_month()
        self.team_store.set_period(year, month)
        names = [s.name for s in self.team_store.sections]
        dlg = AddTeamMemberDialog(self, names)
        if dlg.exec() != QDialog.Accepted:
            return
        payload = dlg.payload()

        section_name = payload["team_name"]
        if section_name == "+ Novo time":
            try:
                section = self.team_store.create_section(payload["new_team_name"])
            except ValueError as e:
                QMessageBox.warning(self, "Adicionar funcionário", str(e))
                return
        else:
            section = next((s for s in self.team_store.sections if s.name == section_name), None)
            if not section:
                QMessageBox.warning(self, "Adicionar funcionário", "Time não encontrado.")
                return

        names = split_member_names(payload["names"])
        if not names:
            QMessageBox.warning(self, "Adicionar funcionário", "Informe ao menos um nome válido.")
            return

        try:
            for member_name in names:
                self.team_store.add_member(section.id, member_name)
        except ValueError as e:
            QMessageBox.warning(self, "Adicionar funcionário", str(e))
            return
        self.refresh_team_control()

    def _bulk_fill_team_cells(self, table: QTableWidget, indexes, code: str) -> bool:
        if not indexes:
            return False

        footer_row = table.rowCount() - 1
        targets: List[tuple[int, int]] = []
        for idx in indexes:
            row = idx.row()
            col = idx.column()
            if row < 0 or col <= 0 or row >= footer_row:
                continue
            member_item = table.item(row, 0)
            if not member_item or not str(member_item.data(Qt.UserRole) or ""):
                continue
            targets.append((row, col))

        if not targets:
            return False

        table.blockSignals(True)
        try:
            for row, col in targets:
                it = table.item(row, col)
                if it is None:
                    it = QTableWidgetItem("")
                    it.setTextAlignment(Qt.AlignCenter)
                    table.setItem(row, col, it)
                it.setText(code)
        finally:
            table.blockSignals(False)

        year, month = self._selected_year_month()
        self.team_store.set_period(year, month)
        section_id = str(table.property("sectionId") or "")
        if not section_id:
            return False

        updates: List[tuple[str, int, str]] = []
        for row, col in targets:
            member_item = table.item(row, 0)
            member_id = str(member_item.data(Qt.UserRole) or "")
            if member_id:
                updates.append((member_id, col, code))

        if not updates:
            return False

        for member_id, day, value in updates:
            self.team_store.set_entry(section_id, member_id, date(year, month, day), value)

        self.refresh_team_control()
        return True

    def _on_team_table_item_changed(self, item: QTableWidgetItem):
        table = self.sender()
        if not isinstance(table, QTableWidget):
            return
        year, month = self._selected_year_month()
        self.team_store.set_period(year, month)
        section_id = str(table.property("sectionId") or "")
        if not section_id:
            return

        footer_row = table.rowCount() - 1
        if item.row() == footer_row:
            return

        member_item = table.item(item.row(), 0)
        if not member_item:
            return
        member_id = str(member_item.data(Qt.UserRole) or "")
        if not member_id:
            return

        if item.column() == 0:
            try:
                self.team_store.rename_member(section_id, member_id, item.text())
            except ValueError as e:
                QMessageBox.warning(self, "Nome", str(e))
            self.refresh_team_control()
            return

        day = item.column()
        if day < 1:
            return
        code = (item.text() or "").strip().upper()
        if code and code not in STATUS_COLORS:
            QMessageBox.warning(self, "Legenda inválida", "Use apenas: F, A, P, D, R, H, K.")
            self.refresh_team_control()
            return

        if code != (item.text() or ""):
            table.blockSignals(True)
            item.setText(code)
            table.blockSignals(False)

        try:
            self.team_store.set_entry(section_id, member_id, date(year, month, day), code)
        except ValueError as e:
            QMessageBox.warning(self, "Legenda", str(e))
            return
        self.refresh_team_control()

    def _open_member_context_menu(self, pos):
        table = self.sender()
        if not isinstance(table, QTableWidget):
            return
        row = table.rowAt(pos.y())
        if row < 0 or row == table.rowCount() - 1:
            return
        member_item = table.item(row, 0)
        if not member_item:
            return

        menu = QMenu(table)
        copy_names_action = menu.addAction("Copiar Nome(s)")
        delete_action = menu.addAction("Excluir")
        picked = menu.exec(table.viewport().mapToGlobal(pos))
        if picked == copy_names_action:
            names = selected_member_names(table)
            if not names:
                QMessageBox.information(self, "Copiar Nome(s)", "Selecione ao menos um nome para copiar.")
                return

            year, month = self._selected_year_month()
            dlg = CopyTeamMembersDialog(self, self.team_store, names, year, month)
            if dlg.exec() != QDialog.Accepted:
                return

            payload = dlg.payload()
            try:
                copied = self.team_store.copy_members_to_section(
                    target_year=int(payload["year"]),
                    target_month=int(payload["month"]),
                    target_section_id=payload["section_id"],
                    names=names,
                )
            except ValueError as e:
                QMessageBox.warning(self, "Copiar Nome(s)", str(e))
                return

            if copied > 0:
                QMessageBox.information(
                    self,
                    "Copiar Nome(s)",
                    f"{copied} nome(s) copiado(s) para o time '{payload['section_name']}'.",
                )
            self.refresh_team_control()
            return
        if picked != delete_action:
            return

        year, month = self._selected_year_month()
        self.team_store.set_period(year, month)
        section_id = str(table.property("sectionId") or "")
        members = selected_members_with_ids(table)
        if not members:
            selected_member_id = str(member_item.data(Qt.UserRole) or "")
            selected_member_name = (member_item.text() or "").strip()
            if not selected_member_id or not selected_member_name:
                return
            members = [(selected_member_id, selected_member_name)]

        dlg = DeleteTeamMembersDialog(self)
        dlg.preload_members(members)
        if dlg.exec() != QDialog.Accepted:
            return

        for member_id in dlg.selected_member_ids():
            self.team_store.remove_member(section_id, member_id)
        dlg.reset_state()
        self.refresh_team_control()

    # Tabs
    def _init_tab1(self):
        tab = QWidget()
        self.t1_date = QDateEdit(QDate.currentDate())
        self.t1_date.setCalendarPopup(True)
        self.t1_date.setDisplayFormat(DATE_FMT_QT)

        consult_btn = QPushButton("Consultar")
        consult_btn.clicked.connect(self.refresh_tab1)

        self.t1_table = self._make_table()

        top = QHBoxLayout()
        self.t1_actions_layout = top
        top.addWidget(QLabel("Selecionar data de consulta:"))
        top.addWidget(self.t1_date)
        top.addWidget(consult_btn)
        top.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.t1_table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Consultar Pendências")

    def _init_tab3(self):
        tab = QWidget()
        self.t3_search = QLineEdit()
        self.t3_search.setPlaceholderText("Buscar em Projeto, Descrição ou Responsável")
        self.t3_status = QComboBox()
        self.t3_status.addItem("")
        self.t3_status.addItems(STATUS_EDIT_OPTIONS)
        self.t3_prioridade = QComboBox()
        self.t3_prioridade.addItem("")
        self.t3_prioridade.addItems(PRIORIDADE_EDIT_OPTIONS)
        self.t3_responsavel = QLineEdit()
        self.t3_responsavel.setPlaceholderText("Filtrar por responsável")

        apply_btn = QPushButton("Aplicar filtros")
        apply_btn.clicked.connect(self.refresh_tab3)

        self.t3_pending_card = QLabel("Pendentes: 0")
        self.t3_delayed_card = QLabel("Em atraso: 0")
        self.t3_done_card = QLabel("Concluídas: 0")

        self.t3_table = self._make_table()

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Busca:"))
        filters.addWidget(self.t3_search, 2)
        filters.addWidget(QLabel("Status:"))
        filters.addWidget(self.t3_status)
        filters.addWidget(QLabel("Prioridade:"))
        filters.addWidget(self.t3_prioridade)
        filters.addWidget(QLabel("Responsável:"))
        filters.addWidget(self.t3_responsavel)
        filters.addWidget(apply_btn)

        cards = QHBoxLayout()
        cards.addWidget(self.t3_pending_card)
        cards.addWidget(self.t3_delayed_card)
        cards.addWidget(self.t3_done_card)
        cards.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(filters)
        layout.addLayout(cards)
        layout.addWidget(self.t3_table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Todas demandas pendentes")

    def _init_tab4(self):
        tab = QWidget()
        self.t4_start = QDateEdit(QDate.currentDate().addDays(-7))
        self.t4_end = QDateEdit(QDate.currentDate())
        self.t4_start.setCalendarPopup(True)
        self.t4_end.setCalendarPopup(True)
        self.t4_start.setDisplayFormat(DATE_FMT_QT)
        self.t4_end.setDisplayFormat(DATE_FMT_QT)

        btn = QPushButton("Consultar")
        btn.clicked.connect(self.refresh_tab4)

        self.t4_table = self._make_table()

        top = QHBoxLayout()
        top.addWidget(QLabel("Início:"))
        top.addWidget(self.t4_start)
        top.addWidget(QLabel("Fim:"))
        top.addWidget(self.t4_end)
        top.addWidget(btn)
        top.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.t4_table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Consultar Demandas Concluídas")

    # Refresh
    def refresh_all(self):
        self.store.load()
        self.refresh_tab1()
        self.refresh_team_control()
        self.refresh_tab3()
        self.refresh_tab4()

    def refresh_current(self):
        i = self.tabs.currentIndex()
        if i == 0:
            self.refresh_tab1()
        elif i == 1:
            self.refresh_team_control()
        elif i == 2:
            self.refresh_tab3()
        elif i == 3:
            self.refresh_tab4()

    def refresh_tab1(self):
        d = qdate_to_date(self.t1_date.date())
        self._fill(self.t1_table, self.store.tab1_by_prazo_date(d))

    def refresh_tab3(self):
        rows = self.store.tab_pending_all()
        filtered = filter_rows(
            rows,
            text_query=self.t3_search.text(),
            status=self.t3_status.currentText(),
            prioridade=self.t3_prioridade.currentText(),
            responsavel=self.t3_responsavel.text(),
        )
        counts = summary_counts(rows)
        self.t3_pending_card.setText(f"Pendentes: {counts['pending']}")
        self.t3_delayed_card.setText(f"Em atraso: {counts['delayed']}")
        self.t3_done_card.setText(f"Concluídas: {counts['concluded']}")
        self._fill(self.t3_table, filtered)
        self._save_preferences()

    def refresh_tab4(self):
        s = qdate_to_date(self.t4_start.date())
        e = qdate_to_date(self.t4_end.date())
        if e < s:
            QMessageBox.warning(self, "Datas inválidas", "A data fim não pode ser menor que a data início.")
            return
        self._fill(self.t4_table, self.store.tab_concluidas_between(s, e))

    # Actions
    def new_demand(self):
        dlg = NewDemandDialog(self)
        if dlg.exec() == QDialog.Accepted:
            try:
                self.store.add(dlg.payload())
            except ValidationError as ve:
                QMessageBox.warning(self, "Validação", str(ve))
            self.refresh_all()

    def export_team_control_csv(self):
        year, month = self._selected_year_month()
        self.team_store.load()
        self.team_store.set_period(year, month)
        default_name = f"controle_time_{year}_{month:02d}.csv"
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar relatório de controle de time",
            os.path.join(self.store.base_dir, default_name),
            "CSV (*.csv)",
        )
        if not export_path:
            return
        if not export_path.lower().endswith(".csv"):
            export_path = f"{export_path}.csv"

        with open(export_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            for row in build_team_control_report_rows(self.team_store.sections, year, month):
                writer.writerow(row)

        QMessageBox.information(self, "Relatório baixado", "Relatório CSV salvo com sucesso.")

    def export_demands_csv(self):
        default_name = "demandas_export.csv"
        default_path = os.path.join(self.store.base_dir, default_name)
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar demandas",
            default_path,
            "CSV (*.csv)",
        )
        if not export_path:
            return

        if not export_path.lower().endswith(".csv"):
            export_path = f"{export_path}.csv"

        selected_rows = self._selected_rows_from_current_tab()
        rows_to_export = selected_rows if selected_rows else self.store.build_view()

        try:
            total = self.store.export_rows_to_csv(export_path, rows_to_export)
        except Exception as e:
            QMessageBox.warning(self, "Falha na exportação", f"Não foi possível exportar o CSV.\n\n{e}")
            return

        QMessageBox.information(self, "Exportação concluída", f"CSV exportado com sucesso.\nTotal de demandas: {total}")

    def import_demands_csv(self):
        default_path = self.store.base_dir
        import_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar demandas",
            default_path,
            "CSV (*.csv)",
        )
        if not import_path:
            return

        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("Confirmar importação")
        confirm_box.setIcon(QMessageBox.Warning)
        confirm_box.setText(
            "Atenção!\n\nAo fazer a importação todos os dados anteriores serão perdidos.\nDeseja prosseguir?"
        )
        import_button = confirm_box.addButton("Importar", QMessageBox.AcceptRole)
        confirm_box.addButton("Cancelar", QMessageBox.RejectRole)
        confirm_box.exec()
        if confirm_box.clickedButton() is not import_button:
            return

        try:
            total = self.store.import_from_exported_csv(import_path)
        except ValidationError as ve:
            QMessageBox.warning(self, "Falha na importação", str(ve))
            return
        except Exception as e:
            QMessageBox.warning(self, "Falha na importação", f"Não foi possível importar o CSV.\n\n{e}")
            return

        self.refresh_all()
        QMessageBox.information(self, "Importação concluída", f"CSV importado com sucesso.\nTotal de demandas: {total}")

    def delete_demand(self):
        selected_rows = self._selected_rows_from_current_tab(include_current=False)
        if selected_rows and self.tabs.currentIndex() == 3:
            QMessageBox.warning(self, "Bloqueado", "Demandas concluídas não podem ser excluídas.")
            return

        dlg = DeleteDemandDialog(self, self.store)
        if selected_rows and self.tabs.currentIndex() in (0, 2):
            dlg.preload_selected_rows(selected_rows)
        if dlg.exec() == QDialog.Accepted:
            self.refresh_all()

    def _selected_rows_from_current_tab(self, include_current: bool = True) -> List[Dict[str, Any]]:
        table = self._table_from_current_tab()
        if not table:
            return []

        selected_indexes = table.selectionModel().selectedRows()
        if not selected_indexes and include_current:
            row_idx = table.currentRow()
            if row_idx < 0:
                return []
            selected_indexes = [table.model().index(row_idx, 0)]
        elif not selected_indexes:
            return []

        row_numbers = sorted(idx.row() for idx in selected_indexes)
        rows_data: List[Dict[str, Any]] = []
        for row_idx in row_numbers:
            row_data: Dict[str, Any] = {}
            for col_idx, col_name in enumerate(VISIBLE_COLUMNS):
                item = table.item(row_idx, col_idx)
                if not item:
                    continue
                row_data[col_name] = item.text()
                if "_id" not in row_data:
                    _id = item.data(Qt.UserRole)
                    if _id:
                        row_data["_id"] = _id
            if row_data.get("_id"):
                rows_data.append(row_data)

        return rows_data

    def _table_from_current_tab(self) -> Optional[QTableWidget]:
        current_tab = self.tabs.currentIndex()
        if current_tab == 0:
            return self.t1_table
        if current_tab == 2:
            return self.t3_table
        if current_tab == 3:
            return self.t4_table
        return None

    def closeEvent(self, event):
        self._save_preferences()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    icon_path = _app_icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    storage_root = resolve_storage_root(sys.argv[0])
    base_dir = ensure_storage_root(storage_root)
    if not base_dir:
        QMessageBox.critical(
            None,
            "Primeira instalação",
            (
                f"Não foi possível criar a pasta obrigatória em '{storage_root}'.\n\n"
                "Crie essa pasta manualmente e abra o software novamente."
            ),
        )
        sys.exit(1)

    store = CsvStore(base_dir)
    win = MainWindow(store)
    win.resize(1280, 720)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
