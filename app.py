from __future__ import annotations

import os
import sys
from datetime import date
from typing import Dict, Any, List, Optional, Tuple

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton,
    QTableWidget, QTableWidgetItem,
    QMessageBox, QInputDialog,
    QDialog, QFormLayout,
    QDateEdit, QLineEdit, QTextEdit, QComboBox,
    QListWidget
)
from PySide6.QtWidgets import QStyledItemDelegate

from csv_store import CsvStore
from validation import ValidationError, normalize_prazo_text, validate_payload

EXEC_NAME = os.path.basename(sys.argv[0]).lower()
DEBUG_MODE = "debug" in EXEC_NAME

DATE_FMT_QT = "dd/MM/yyyy"


def debug_msg(title: str, text: str):
    if DEBUG_MODE:
        QMessageBox.information(None, title, text)


def qdate_to_date(qd: QDate) -> date:
    return date(qd.year(), qd.month(), qd.day())


VISIBLE_COLUMNS = [
    "Linha", "É Urgente?", "Status", "Timing", "Prioridade",
    "Data de Registro", "Prazo", "Data Conclusão",
    "Projeto", "Descrição", "ID Azure", "% Conclusão",
    "Responsável", "Reportar?", "Nome", "Time/Função"
]

# Campos que só podem ser editados via picker
PICKER_ONLY = {"Data de Registro", "Prazo", "Data Conclusão"}

# Timing e Linha não editáveis
NON_EDITABLE = {"Linha", "Timing"} | PICKER_ONLY

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


class ColumnComboDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, column_to_options: Dict[int, List[str]] | None = None):
        super().__init__(parent)
        self.column_to_options = column_to_options or {}

    def createEditor(self, parent, option, index):
        col = index.column()
        if col in self.column_to_options:
            combo = QComboBox(parent)
            combo.setEditable(False)
            combo.addItems(self.column_to_options[col])
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


class DatePickDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, label: str, allow_clear: bool = False):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat(DATE_FMT_QT)

        self._cleared = False

        form = QFormLayout()
        form.addRow(label, self.date_edit)

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

    def was_cleared(self) -> bool:
        return self._cleared

    def selected_date_str(self) -> str:
        return qdate_to_date(self.date_edit.date()).strftime("%d/%m/%Y")


class PrazoMultiDialog(QDialog):
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


class DeleteDemandDialog(QDialog):
    """
    Exclusão por Linha:
    - usuário informa Linha
    - app carrega Projeto, Prazo e Descrição
    - confirma excluir
    - bloqueia se Status == Concluído
    """
    def __init__(self, parent: QWidget, store: CsvStore):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Excluir demanda")

        self.line_input = QLineEdit()
        self.line_input.setPlaceholderText("Ex: 12")

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)

        self.load_btn = QPushButton("Carregar")
        self.load_btn.clicked.connect(self._load_line)

        self.delete_btn = QPushButton("Excluir")
        self.cancel_btn = QPushButton("Cancelar")
        self.delete_btn.clicked.connect(self._do_delete)
        self.cancel_btn.clicked.connect(self.reject)

        self.delete_btn.setEnabled(False)
        self._loaded_id: Optional[str] = None
        self._loaded_line: Optional[int] = None

        form = QFormLayout()
        form.addRow("Número da Linha*", self.line_input)

        top = QHBoxLayout()
        top.addWidget(self.load_btn)
        top.addStretch()

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

    def _load_line(self):
        raw = (self.line_input.text() or "").strip()
        if not raw.isdigit():
            QMessageBox.warning(self, "Inválido", "Informe um número de linha válido.")
            self._loaded_id = None
            self._loaded_line = None
            self.delete_btn.setEnabled(False)
            self.info_label.setText("")
            return

        line = int(raw)
        self.store.load()
        view = self.store.build_view()

        if line < 1 or line > len(view):
            QMessageBox.warning(self, "Não encontrado", f"Nenhuma demanda encontrada na Linha {line}.")
            self._loaded_id = None
            self._loaded_line = None
            self.delete_btn.setEnabled(False)
            self.info_label.setText("")
            return

        row = view[line - 1]
        _id = row.get("_id")
        status = (row.get("Status") or "").strip()

        self._loaded_id = _id
        self._loaded_line = line

        projeto = row.get("Projeto", "")
        prazo = row.get("Prazo", "")
        desc = row.get("Descrição", "")

        self.info_label.setText(
            f"**Linha {line}**\n"
            f"Projeto: {projeto}\n"
            f"Prazo: {prazo}\n"
            f"Descrição: {desc}\n"
            f"Status: {status}"
        )

        if status == "Concluído":
            self.delete_btn.setEnabled(False)
            QMessageBox.warning(self, "Bloqueado", "Demandas concluídas não podem ser excluídas.")
        else:
            self.delete_btn.setEnabled(True)

    def _do_delete(self):
        if not self._loaded_id or not self._loaded_line:
            return

        self.store.load()
        dr = self.store.get(self._loaded_id)
        if dr and (dr.data.get("Status") or "").strip() == "Concluído":
            QMessageBox.warning(self, "Bloqueado", "Demandas concluídas não podem ser excluídas.")
            self.reject()
            return

        ok = self.store.delete_by_id(self._loaded_id)
        if not ok:
            QMessageBox.warning(self, "Falha", "Não foi possível excluir. Verifique a Linha e tente novamente.")
            self.reject()
            return

        self.accept()


class NewDemandDialog(QDialog):
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
        self.descricao = QTextEdit()

        self.urgente = QComboBox()
        self.urgente.setEditable(False)
        self.urgente.addItem("")
        self.urgente.addItems(URGENCIA_EDIT_OPTIONS)

        self.projeto = QLineEdit()
        self.id_azure = QLineEdit()

        self.perc = QComboBox()
        self.perc.setEditable(False)
        for label, _val in PERCENT_OPTIONS:
            self.perc.addItem(label)

        self.reportar = QComboBox()
        self.reportar.setEditable(False)
        self.reportar.addItem("")
        self.reportar.addItems(REPORTAR_EDIT_OPTIONS)

        self.nome = QLineEdit()
        self.time_funcao = QLineEdit()

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

        form = QFormLayout()
        form.addRow("Status*", self.status)
        form.addRow("Prioridade*", self.prioridade)
        form.addRow("Data de Registro*", self.data_registro)
        form.addRow("Responsável*", self.responsavel)
        form.addRow("Descrição*", self.descricao)

        form.addRow("É Urgente?", self.urgente)
        form.addRow("Projeto", self.projeto)
        form.addRow("ID Azure", self.id_azure)
        form.addRow("% Conclusão", self.perc)
        form.addRow("Data Conclusão", conc_row)
        form.addRow("Reportar?", self.reportar)
        form.addRow("Nome", self.nome)
        form.addRow("Time/Função", self.time_funcao)

        prazo_box = QVBoxLayout()
        prazo_box.addWidget(self.prazo_label)
        line = QHBoxLayout()
        line.addWidget(self.prazo_picker)
        line.addWidget(add_prazo)
        prazo_box.addLayout(line)
        prazo_box.addWidget(self.prazo_list)
        prazo_box.addWidget(rem_prazo)

        btns = QHBoxLayout()
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)

        root = QVBoxLayout()
        root.addLayout(form)
        root.addLayout(prazo_box)
        root.addLayout(btns)
        self.setLayout(root)

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
        missing = []
        if not self.descricao.toPlainText().strip():
            missing.append("Descrição")
        if not self.prioridade.currentText().strip():
            missing.append("Prioridade")
        if not self.status.currentText().strip():
            missing.append("Status")
        if not self.responsavel.text().strip():
            missing.append("Responsável")
        if self.prazo_list.count() == 0:
            missing.append("Prazo (adicione ao menos uma data)")

        wants_concluded = (self.status.currentText().strip() == "Concluído") or (self.perc.currentText().startswith("100%"))
        if wants_concluded and not self._conclusao_txt.strip():
            missing.append("Data Conclusão (obrigatória quando Concluído/100%)")

        if missing:
            QMessageBox.warning(
                self,
                "Campos obrigatórios",
                "Os seguintes campos obrigatórios não foram preenchidos:\n\n- " + "\n- ".join(missing)
            )
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


class MainWindow(QMainWindow):
    def __init__(self, store: CsvStore):
        super().__init__()
        self.store = store
        self.setWindowTitle("DemandasApp")

        self._filling = False

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._init_tab1()
        self._init_tab3()
        self._init_tab4()

        self.refresh_all()
        self.tabs.currentChanged.connect(self._on_tab_changed)

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
        table.resizeColumnsToContents()
        return table

    def _set_item(self, table: QTableWidget, r: int, c: int, text: str, _id: str):
        it = QTableWidgetItem(text or "")
        colname = VISIBLE_COLUMNS[c]

        if colname in NON_EDITABLE:
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)

        it.setData(Qt.UserRole, _id)

        # guarda valor anterior do status
        if colname == "Status":
            it.setData(Qt.UserRole + 1, text or "")

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

    def _on_tab_changed(self, idx: int):
        self.refresh_current()

    # Tabs
    def _init_tab1(self):
        tab = QWidget()
        self.t1_date = QDateEdit(QDate.currentDate())
        self.t1_date.setCalendarPopup(True)
        self.t1_date.setDisplayFormat(DATE_FMT_QT)

        btn = QPushButton("Consultar")
        btn.clicked.connect(self.refresh_tab1)

        new_btn = QPushButton("Nova demanda")
        new_btn.clicked.connect(self.new_demand)

        del_btn = QPushButton("Excluir demanda")
        del_btn.clicked.connect(self.delete_demand)

        self.t1_table = self._make_table()

        top = QHBoxLayout()
        top.addWidget(QLabel("Selecionar data de consulta:"))
        top.addWidget(self.t1_date)
        top.addWidget(btn)
        top.addStretch()
        top.addWidget(new_btn)
        top.addWidget(del_btn)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.t1_table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Consulta de pendências por data")

    def _init_tab3(self):
        tab = QWidget()
        self.t3_table = self._make_table()
        layout = QVBoxLayout()
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
        self.tabs.addTab(tab, "Consultar demandas concluídas entre datas")

    # Refresh
    def refresh_all(self):
        self.store.load()
        self.refresh_tab1()
        self.refresh_tab3()
        self.refresh_tab4()

    def refresh_current(self):
        i = self.tabs.currentIndex()
        if i == 0:
            self.refresh_tab1()
        elif i == 1:
            self.refresh_tab3()
        elif i == 2:
            self.refresh_tab4()

    def refresh_tab1(self):
        d = qdate_to_date(self.t1_date.date())
        self._fill(self.t1_table, self.store.tab1_by_prazo_date(d))

    def refresh_tab3(self):
        self._fill(self.t3_table, self.store.tab_pending_all())

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

    def delete_demand(self):
        dlg = DeleteDemandDialog(self, self.store)
        if dlg.exec() == QDialog.Accepted:
            self.refresh_all()


def main():
    app = QApplication(sys.argv)
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    store = CsvStore(base_dir)
    win = MainWindow(store)
    win.resize(1280, 720)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
