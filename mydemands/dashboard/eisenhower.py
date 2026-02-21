from __future__ import annotations

from typing import Any, Callable, Dict, List

from PySide6.QtCore import QEvent, QPoint, QSize, Qt, Signal
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
    def __init__(
        self,
        row: Dict[str, Any],
        on_click: Callable[[Dict[str, Any], QWidget], None],
        on_double_click: Callable[[Dict[str, Any]], None],
        on_context_menu: Callable[[Dict[str, Any], QPoint], None],
    ):
        super().__init__()
        self._row = row
        self._on_click = on_click
        self._on_double_click = on_double_click
        self._on_context_menu = on_context_menu
        self.setObjectName("eisenhowerDemandCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(116)
        self.setProperty("selected", False)
        self.setProperty("dragging", False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        demand_number = str(row.get("ID") or row.get("_id") or "-")

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)
        id_label = QLabel(f"#{demand_number}")
        id_label.setObjectName("eisenhowerDemandId")
        top_row.addWidget(id_label)
        top_row.addStretch()

        for value, badge_type in (
            (row.get("Prioridade") or "Média", "priority"),
            (row.get("Timing") or "Sem prazo", "timing"),
            (row.get("É Urgente?") or "Não", "urgent"),
        ):
            badge = QLabel(str(value))
            badge.setObjectName("eisenhowerStatusBadge")
            badge.setProperty("badgeType", badge_type)
            top_row.addWidget(badge)

        desc_label = QLabel()
        desc_label.setObjectName("eisenhowerDescription")
        desc_label.setWordWrap(False)
        desc_label.setTextInteractionFlags(Qt.NoTextInteraction)
        desc_label.setToolTip((row.get("Descrição") or "Sem descrição").strip())

        meta_parts = []
        if (row.get("Projeto") or "").strip():
            meta_parts.append(f"Projeto: {row.get('Projeto')}")
        if (row.get("Prazo") or "").strip():
            meta_parts.append(f"Prazo: {row.get('Prazo')}")
        info = QLabel(" • ".join(meta_parts) or "Sem metadados")
        info.setObjectName("eisenhowerMetaInfo")
        info.setWordWrap(False)

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
        self._desc_label.setText(f"{first}\n{metrics.elidedText(leftover, Qt.ElideRight, width)}" if leftover else first)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._set_description()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._on_click(self._row, self)
        if event.button() == Qt.RightButton:
            self._on_context_menu(self._row, event.globalPosition().toPoint())

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if event.button() == Qt.LeftButton:
            self._on_double_click(self._row)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_dragging(self, dragging: bool) -> None:
        self.setProperty("dragging", dragging)
        self.style().unpolish(self)
        self.style().polish(self)


class QuadrantListWidget(QListWidget):
    def __init__(
        self,
        quadrant_key: str,
        on_card_click: Callable[[Dict[str, Any], QWidget], None],
        on_card_double_click: Callable[[Dict[str, Any]], None],
        on_card_context_menu: Callable[[Dict[str, Any], QPoint], None],
        on_move_request: Callable[[str, str, Dict[str, Any]], bool] | None = None,
    ):
        super().__init__()
        self.quadrant_key = quadrant_key
        self._on_card_click = on_card_click
        self._on_card_double_click = on_card_double_click
        self._on_card_context_menu = on_card_context_menu
        self._on_move_request = on_move_request
        self.setObjectName(f"{quadrant_key}_list")
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSpacing(10)

    def add_row(self, row: Dict[str, Any], target_index: int | None = None) -> None:
        item = QListWidgetItem()
        item.setData(Qt.UserRole, row)
        item.setSizeHint(QSize(0, 116))
        if isinstance(target_index, int) and 0 <= target_index <= self.count():
            self.insertItem(target_index, item)
        else:
            self.addItem(item)
        self.setItemWidget(item, DemandMiniCard(row, self._on_card_click, self._on_card_double_click, self._on_card_context_menu))

    def _update_dragover(self, enabled: bool) -> None:
        self.setProperty("dragover", enabled)
        self.style().unpolish(self)
        self.style().polish(self)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        widget = self.itemWidget(item) if item else None
        if widget is not None:
            widget.set_dragging(True)
            pix = widget.grab()
            drag = QDrag(self)
            drag.setMimeData(self.mimeData(self.selectedItems()))
            drag.setPixmap(pix)
            drag.exec(Qt.MoveAction)
            widget.set_dragging(False)
            return
        super().startDrag(supportedActions)

    def dragEnterEvent(self, event):
        if isinstance(event.source(), QuadrantListWidget):
            event.acceptProposedAction()
            self._update_dragover(True)
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if isinstance(event.source(), QuadrantListWidget):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        super().dragLeaveEvent(event)
        self._update_dragover(False)

    def dropEvent(self, event):
        source = event.source()
        self._update_dragover(False)
        if not isinstance(source, QuadrantListWidget):
            event.ignore()
            return

        source_item = source.currentItem()
        row = source_item.data(Qt.UserRole) if source_item else None
        if not isinstance(row, dict):
            event.ignore()
            return

        target_index = self.indexAt(event.position().toPoint()).row()
        if target_index < 0:
            target_index = self.count()

        if source is self:
            super().dropEvent(event)
            return

        source_row_idx = source.row(source_item)
        source.takeItem(source_row_idx)
        self.add_row(row, target_index)
        self.setCurrentRow(target_index)

        moved_ok = bool(self._on_move_request and self._on_move_request(source.quadrant_key, self.quadrant_key, row))
        if moved_ok:
            event.acceptProposedAction()
            return

        rollback_item = self.takeItem(target_index)
        del rollback_item
        source.add_row(row, source_row_idx)
        source.setCurrentRow(source_row_idx)
        event.ignore()


class EisenhowerView(QWidget):
    context_action_requested = Signal(str, dict)

    def __init__(
        self,
        on_card_double_click,
        on_move_card: Callable[[str, str, Dict[str, Any]], bool] | None = None,
        classifier: EisenhowerClassifierService | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._on_card_double_click = on_card_double_click
        self._classifier = classifier or EisenhowerClassifierService()
        self._dnd_controller = EisenhowerDnDController(on_move_card) if on_move_card else None
        self.last_groups: Dict[str, List[Dict[str, Any]]] = {q.key: [] for q in QUADRANTS}
        self._columns_lists: Dict[str, QuadrantListWidget] = {}
        self._selected_card_widget: DemandMiniCard | None = None
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
            title.setObjectName("eisenhowerQuadrantTitle")
            count = QLabel("0")
            count.setObjectName(f"{quadrant.key}_count")

            header = QVBoxLayout()
            header.setSpacing(2)
            header.addWidget(title, alignment=Qt.AlignHCenter)
            header.addWidget(count, alignment=Qt.AlignHCenter)

            list_widget = QuadrantListWidget(
                quadrant.key,
                self._select_card,
                self._on_card_double_click,
                self._show_context_menu,
                self._handle_move_request,
            )
            list_widget.setObjectName(f"{quadrant.key}_list")
            list_widget.viewport().installEventFilter(self)
            list_widget.setStyleSheet(
                f"QListWidget#{quadrant.key}_list {{"
                f"border: 1px solid {color_tokens[quadrant.key]['border']};"
                f"border-top: 4px solid {color_tokens[quadrant.key]['accent']};"
                f"border-radius: 10px; background: {color_tokens[quadrant.key]['background']}; padding: 8px;}}"
                f"QListWidget#{quadrant.key}_list[dragover='true'] {{border: 2px dashed {color_tokens[quadrant.key]['accent']}; background: {color_tokens[quadrant.key]['dragover_background']};}}"
                f"QWidget#eisenhowerDemandCard {{border: 1px solid {color_tokens[quadrant.key]['card_border']}; border-radius: 10px;"
                f" background: {color_tokens[quadrant.key]['card_background']}; margin-bottom: 10px;}}"
                f"QWidget#eisenhowerDemandCard:hover {{border-color: {color_tokens[quadrant.key]['hover_border']}; background: {color_tokens[quadrant.key]['hover_background']};}}"
                f"QWidget#eisenhowerDemandCard[selected='true'] {{border: 2px solid {color_tokens[quadrant.key]['accent']};}}"
                f"QWidget#eisenhowerDemandCard[dragging='true'] {{border: 2px dashed {color_tokens[quadrant.key]['accent']}; background: {color_tokens[quadrant.key]['dragging_background']};}}"
                "QLabel#eisenhowerDemandId {font-weight: 700;}"
                "QLabel#eisenhowerStatusBadge {font-size: 10px; border-radius: 8px; padding: 1px 6px; background: rgba(128,128,128,0.25);}"
                f"QLabel#eisenhowerDescription {{font-size: 12px; color: {color_tokens[quadrant.key]['text_primary']};}}"
                f"QLabel#eisenhowerMetaInfo {{font-size: 11px; color: {color_tokens[quadrant.key]['text_secondary']};}}"
                f"QLabel#eisenhowerQuadrantTitle {{color: {color_tokens[quadrant.key]['label_color']}; font-weight: 700;}}"
            )
            self._columns_lists[quadrant.key] = list_widget

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(list_widget)

            column_layout.addLayout(header)
            column_layout.addWidget(scroll)
            root.addWidget(column, 1)

    @staticmethod
    def _build_color_tokens(is_dark: bool) -> Dict[str, Dict[str, str]]:
        base = {
            "q1": "#ff6b6b" if is_dark else "#d73a49",
            "q2": "#ffd166" if is_dark else "#bf8700",
            "q3": "#62d48f" if is_dark else "#2da44e",
            "q4": "#72b7ff" if is_dark else "#1f6feb",
        }
        if is_dark:
            return {
                key: {
                    "accent": accent,
                    "border": "#334155",
                    "background": "#0f172a",
                    "dragover_background": "#111f36",
                    "card_background": "#1e293b",
                    "card_border": "#475569",
                    "hover_border": accent,
                    "hover_background": "#243246",
                    "dragging_background": "#243246",
                    "label_color": "#f8fafc",
                    "text_primary": "#f8fafc",
                    "text_secondary": "#cbd5e1",
                }
                for key, accent in base.items()
            }
        return {
            key: {
                "accent": accent,
                "border": "#D0D7E2",
                "background": "#F7F9FC",
                "dragover_background": "#EFF4FB",
                "card_background": "#FFFFFF",
                "card_border": "#D0D7E2",
                "hover_border": accent,
                "hover_background": "#F8FAFF",
                "dragging_background": "#EEF3FD",
                "label_color": "#1f2937",
                "text_primary": "#111827",
                "text_secondary": "#6b7280",
            }
            for key, accent in base.items()
        }

    def _handle_move_request(self, source_quadrant: str, target_quadrant: str, row: Dict[str, Any]) -> bool:
        if not self._dnd_controller:
            return False
        return self._dnd_controller.handle_move(source_quadrant, target_quadrant, row)

    def _select_card(self, row: Dict[str, Any], card: QWidget) -> None:
        if isinstance(self._selected_card_widget, DemandMiniCard) and self._selected_card_widget is not card:
            self._selected_card_widget.set_selected(False)
        if isinstance(card, DemandMiniCard):
            card.set_selected(True)
            self._selected_card_widget = card

    def clear_selection(self) -> None:
        if isinstance(self._selected_card_widget, DemandMiniCard):
            self._selected_card_widget.set_selected(False)
        self._selected_card_widget = None

    def _show_context_menu(self, row: Dict[str, Any], global_pos: QPoint) -> None:
        self.context_action_requested.emit("open", row | {"_context_pos": global_pos})

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress and hasattr(watched, "parent"):
            list_widget = watched.parent()
            if isinstance(list_widget, QListWidget) and list_widget.itemAt(event.pos()) is None:
                self.clear_selection()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.clear_selection()

    def set_rows(self, rows: List[Dict[str, Any]]) -> None:
        self.clear_selection()
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
