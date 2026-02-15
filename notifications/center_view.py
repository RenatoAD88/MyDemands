from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .models import Notification, NotificationType
from .store import NotificationStore


class NotificationCenterDialog(QDialog):
    def __init__(self, store: NotificationStore, on_open: Callable[[Notification], None], parent=None):
        super().__init__(parent)
        self.store = store
        self.on_open = on_open
        self.setWindowTitle("Central de Notificações")
        self.resize(900, 420)

        self.type_filter = QComboBox()
        self.type_filter.addItem("Todos", None)
        for nt in NotificationType:
            self.type_filter.addItem(nt.value, nt)
        self.read_filter = QComboBox()
        self.read_filter.addItem("Todas", None)
        self.read_filter.addItem("Não lidas", False)
        self.read_filter.addItem("Lidas", True)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Data", "Tipo", "Título", "Mensagem", "Status"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemDoubleClicked.connect(self._open_selected)

        filter_row = QHBoxLayout()
        filter_row.addWidget(self.type_filter)
        filter_row.addWidget(self.read_filter)
        refresh_btn = QPushButton("Filtrar")
        refresh_btn.clicked.connect(self.refresh)
        mark_read_btn = QPushButton("Marcar como lida")
        mark_read_btn.clicked.connect(self.mark_selected_as_read)
        open_btn = QPushButton("Abrir")
        open_btn.clicked.connect(self._open_selected)
        filter_row.addWidget(refresh_btn)
        filter_row.addWidget(mark_read_btn)
        filter_row.addWidget(open_btn)

        root = QVBoxLayout(self)
        root.addLayout(filter_row)
        root.addWidget(self.table)
        self.setLayout(root)
        self.refresh()

    def refresh(self) -> None:
        type_filter = self.type_filter.currentData()
        read_filter = self.read_filter.currentData()
        rows = self.store.list_notifications(type_filter=type_filter, read_filter=read_filter)
        self.table.setRowCount(len(rows))
        for i, n in enumerate(rows):
            self._set_row(i, n)

    def _set_row(self, row: int, n: Notification) -> None:
        values = [
            n.timestamp.strftime("%d/%m/%Y %H:%M"),
            n.type.value,
            n.title,
            n.body,
            "Lida" if n.read else "Não lida",
        ]
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, n.id)
            self.table.setItem(row, col, item)

    def mark_selected_as_read(self) -> None:
        for idx in self.table.selectionModel().selectedRows():
            item = self.table.item(idx.row(), 0)
            if not item:
                continue
            notif_id = item.data(Qt.UserRole)
            if notif_id:
                self.store.mark_as_read(int(notif_id))
        self.refresh()

    def _open_selected(self):
        idxs = self.table.selectionModel().selectedRows()
        if not idxs:
            return
        row = idxs[0].row()
        notif_id = int(self.table.item(row, 0).data(Qt.UserRole))
        notification = next((n for n in self.store.list_notifications(limit=500) if n.id == notif_id), None)
        if not notification:
            return
        self.store.mark_as_read(notif_id)
        self.on_open(notification)
        self.refresh()
