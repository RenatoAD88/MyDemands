from __future__ import annotations

from typing import Any, Callable, Dict, List

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QDrag, QFontMetrics, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from mydemands.dashboard.eisenhower_classifier import QUADRANTS, EisenhowerClassifierService
from mydemands.dashboard.eisenhower_dnd import EisenhowerDnDController


class DemandMiniCard(QWidget):
    def __init__(self, row: Dict[str, Any], on_click: Callable[[Dict[str, Any]], None]):
        super().__init__()
        self._row = row
        self._on_click = on_click
        self.setObjectName("eisenhowerDemandCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(96)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        demand_number = str(row.get("ID") or row.get("_id") or "-")

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)
        id_label = QLabel(f"#{demand_number}")
        id_label.setStyleSheet("font-weight: 700;")
        top_row.addWidget(id_label)

        status = (row.get("Status") or "").strip()
        if status:
            badge = QLabel(status)
            badge.setObjectName("eisenhowerStatusBadge")
            top_row.addWidget(badge)
        top_row.addStretch()

        desc_label = QLabel()
        desc_label.setObjectName("eisenhowerDescription")
        desc_label.setWordWrap(False)
        desc_label.setTextInteractionFlags(Qt.NoTextInteraction)
        desc_label.setToolTip((row.get("Descrição") or "Sem descrição").strip())

        info = QLabel(
            f"Prioridade: {(row.get('Prioridade') or 'Média')}  |  "
            f"Timing: {(row.get('Timing') or 'Sem prazo')}  |  "
            f"Urgente: {(row.get('É Urgente?') or 'Não')}"
        )
        info.setObjectName("eisenhowerMetaInfo")

        layout.addLayout(top_row)
        layout.addWidget(desc_label)
        layout.addWidget(info)

        self._desc_label = desc_label
        self._set_description()

    def _set_description(self) -> None:
        raw = (self._row.get("Descrição") or "Sem descrição").replace("\n", " ").strip()
        metrics = QFontMetrics(self._desc_label.font())
        width = max(self.width() - 24, 50)
        first = metrics.elidedText(raw, Qt.ElideRight, width)
        leftover = raw[len(first.rstrip("…")) :].strip()
        if leftover:
            second = metrics.elidedText(leftover, Qt.ElideRight, width)
            text = f"{first}\n{second}"
        else:
            text = first
        self._desc_label.setText(text)
        self._desc_label.setStyleSheet("line-height: 1.35;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._set_description()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._on_click(self._row)


class QuadrantListWidget(QListWidget):
    move_requested = Signal(str, str, dict)

    def __init__(self, quadrant_key: str, on_card_click: Callable[[Dict[str, Any]], None]):
        super().__init__()
        self.quadrant_key = quadrant_key
        self._on_card_click = on_card_click
        self.setObjectName(f"{quadrant_key}_list")
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSpacing(6)

    def add_row(self, row: Dict[str, Any]) -> None:
        item = QListWidgetItem()
        item.setData(Qt.UserRole, row)
        item.setSizeHint(QSize(0, 96))
        self.addItem(item)
        self.setItemWidget(item, DemandMiniCard(row, self._on_card_click))

    def startDrag(self, supportedActions):
        item = self.currentItem()
        widget = self.itemWidget(item) if item else None
        if widget is not None:
            pix = widget.grab()
            drag = QDrag(self)
            drag.setMimeData(self.mimeData(self.selectedItems()))
            drag.setPixmap(pix)
            drag.exec(Qt.MoveAction)
            return
        super().startDrag(supportedActions)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()
        self.setProperty("dragover", True)
        self.style().unpolish(self)
        self.style().polish(self)

    def dragLeaveEvent(self, event):
        super().dragLeaveEvent(event)
        self.setProperty("dragover", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event):
        source = event.source()
        self.setProperty("dragover", False)
        self.style().unpolish(self)
        self.style().polish(self)

        if not isinstance(source, QuadrantListWidget):
            event.ignore()
            return

        item = source.currentItem()
        row = item.data(Qt.UserRole) if item else None
        if not isinstance(row, dict):
            event.ignore()
            return

        if source.quadrant_key == self.quadrant_key:
            event.acceptProposedAction()
            return

        self.move_requested.emit(source.quadrant_key, self.quadrant_key, row)
        event.acceptProposedAction()


class EisenhowerView(QWidget):
    def __init__(
        self,
        on_card_click,
        on_move_card: Callable[[str, str, Dict[str, Any]], None] | None = None,
        classifier: EisenhowerClassifierService | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._on_card_click = on_card_click
        self._classifier = classifier or EisenhowerClassifierService()
        self._dnd_controller = EisenhowerDnDController(on_move_card) if on_move_card else None
        self.last_groups: Dict[str, List[Dict[str, Any]]] = {q.key: [] for q in QUADRANTS}
        self._columns_lists: Dict[str, QuadrantListWidget] = {}
        root = QHBoxLayout(self)
        root.setSpacing(8)

        palette = QApplication.palette()
        is_dark = palette.color(QPalette.Window).lightness() < 128
        color_tokens = self._build_color_tokens(is_dark)

        for quadrant in QUADRANTS:
            column = QFrame()
            column.setObjectName(f"eisenhowerColumn_{quadrant.key}")
            column.setProperty("accent", color_tokens[quadrant.key]["accent"])
            column.setFrameShape(QFrame.StyledPanel)
            column_layout = QVBoxLayout(column)
            column_layout.setContentsMargins(8, 8, 8, 8)
            column_layout.setSpacing(6)

            title = QLabel(quadrant.title)
            title.setStyleSheet("font-weight: 700;")
            count = QLabel("0")
            count.setObjectName(f"{quadrant.key}_count")
            count.setStyleSheet("font-weight: 700;")

            header = QVBoxLayout()
            header.setSpacing(2)
            header.addWidget(title, alignment=Qt.AlignHCenter)
            header.addWidget(count, alignment=Qt.AlignHCenter)

            list_widget = QuadrantListWidget(quadrant.key, self._on_card_click)
            list_widget.setObjectName(f"{quadrant.key}_list")
            list_widget.setStyleSheet(
                f"QListWidget#{quadrant.key}_list {{"
                f"border: 1px solid {color_tokens[quadrant.key]['border']};"
                f"border-top: 4px solid {color_tokens[quadrant.key]['accent']};"
                f"border-radius: 10px; background: {color_tokens[quadrant.key]['background']}; padding: 6px;}}"
                f"QListWidget#{quadrant.key}_list[dragover='true'] {{border: 2px dashed {color_tokens[quadrant.key]['accent']};}}"
                "QWidget#eisenhowerDemandCard {border: 1px solid rgba(120, 120, 120, 0.35); border-radius: 8px; background: rgba(255,255,255,0.06);}"
                "QWidget#eisenhowerDemandCard:hover {border-color: rgba(110, 170, 255, 0.8);}"
                "QLabel#eisenhowerStatusBadge {font-size: 10px; border-radius: 8px; padding: 1px 6px; background: rgba(128,128,128,0.25);}"
                "QLabel#eisenhowerMetaInfo {font-size: 11px; color: palette(mid);}"
            )
            if self._dnd_controller:
                list_widget.move_requested.connect(self._dnd_controller.handle_move)
            self._columns_lists[quadrant.key] = list_widget

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(list_widget)

            column_layout.addLayout(header)
            column_layout.addWidget(scroll)
            root.addWidget(column, 1)

    @staticmethod
    def _build_color_tokens(is_dark: bool) -> Dict[str, Dict[str, str]]:
        if is_dark:
            return {
                "q1": {"accent": "#ff6b6b", "border": "#8f3d3d", "background": "rgba(255, 70, 70, 0.10)"},
                "q2": {"accent": "#ffd166", "border": "#8f7b34", "background": "rgba(255, 209, 102, 0.10)"},
                "q3": {"accent": "#62d48f", "border": "#3f7f57", "background": "rgba(98, 212, 143, 0.10)"},
                "q4": {"accent": "#72b7ff", "border": "#3d5c8f", "background": "rgba(114, 183, 255, 0.10)"},
            }
        return {
            "q1": {"accent": "#d73a49", "border": "#f0b5bb", "background": "rgba(215, 58, 73, 0.06)"},
            "q2": {"accent": "#bf8700", "border": "#e9d9a2", "background": "rgba(191, 135, 0, 0.07)"},
            "q3": {"accent": "#2da44e", "border": "#b8e1c4", "background": "rgba(45, 164, 78, 0.07)"},
            "q4": {"accent": "#1f6feb", "border": "#bad1f7", "background": "rgba(31, 111, 235, 0.06)"},
        }

    def set_rows(self, rows: List[Dict[str, Any]]) -> None:
        self.last_groups = self._classifier.group_rows(rows)
        for quadrant in QUADRANTS:
            key = quadrant.key
            rows_in_group = self.last_groups.get(key, [])
            list_widget = self._columns_lists[key]
            list_widget.clear()
            for row in rows_in_group:
                list_widget.add_row(row)
            count_label = self.findChild(QLabel, f"{key}_count")
            if count_label is not None:
                count_label.setText(str(len(rows_in_group)))
