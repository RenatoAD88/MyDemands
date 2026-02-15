from __future__ import annotations

from typing import Callable, Optional

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
    def __init__(
        self,
        store: NotificationStore,
        on_open: Callable[[Notification], None],
        on_change: Optional[Callable[[], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.store = store
        self.on_open = on_open
        self.on_change = on_change
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
        self.table.itemSelectionChanged.connect(self._update_mark_button_label)
        self.table.itemDoubleClicked.connect(self._open_selected)

        filter_row = QHBoxLayout()
        filter_row.addWidget(self.type_filter)
        filter_row.addWidget(self.read_filter)
        refresh_btn = QPushButton("Filtrar")
        refresh_btn.clicked.connect(self.refresh)
        self.mark_toggle_btn = QPushButton("Marcar como lida")
        self.mark_toggle_btn.clicked.connect(self.toggle_selected_read_status)
        delete_btn = QPushButton("Excluir")
        delete_btn.clicked.connect(self.delete_selected_notifications)
        filter_row.addWidget(refresh_btn)
        filter_row.addWidget(self.mark_toggle_btn)
        filter_row.addWidget(delete_btn)

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
        self._update_mark_button_label()

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

    def _selected_notification_ids(self) -> list[int]:
        selected_ids: list[int] = []
        for idx in self.table.selectionModel().selectedRows():
            item = self.table.item(idx.row(), 0)
            if not item:
                continue
            notif_id = item.data(Qt.UserRole)
            if notif_id:
                selected_ids.append(int(notif_id))
        return selected_ids

    def _selected_notification(self) -> Notification | None:
        idxs = self.table.selectionModel().selectedRows()
        if not idxs:
            return None
        row = idxs[0].row()
        item = self.table.item(row, 0)
        if not item:
            return None
        notif_id = item.data(Qt.UserRole)
        if not notif_id:
            return None
        return self.store.get_notification_by_id(int(notif_id))

    def _update_mark_button_label(self) -> None:
        notification = self._selected_notification()
        if notification and notification.read:
            self.mark_toggle_btn.setText("Marcar como não lida")
        else:
            self.mark_toggle_btn.setText("Marcar como lida")

    def toggle_selected_read_status(self) -> None:
        selected = self._selected_notification()
        if selected is None:
            return
        ids = self._selected_notification_ids()
        if selected.read:
            for notif_id in ids:
                self.store.mark_as_unread(notif_id)
        else:
            for notif_id in ids:
                self.store.mark_as_read(notif_id)
        self.refresh()
        self._notify_change()

    def delete_selected_notifications(self) -> None:
        ids = self._selected_notification_ids()
        for notif_id in ids:
            self.store.delete_notification(notif_id)
        self.refresh()
        self._notify_change()

    def _open_selected(self):
        notification = self._selected_notification()
        if not notification:
            return
        self.store.mark_as_read(int(notification.id))
        self.on_open(notification)
        self.refresh()
        self._notify_change()

    def _notify_change(self) -> None:
        if self.on_change:
            self.on_change()
