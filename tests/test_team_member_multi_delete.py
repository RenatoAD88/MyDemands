import pytest

qtwidgets = pytest.importorskip("PySide6.QtWidgets", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtcore = pytest.importorskip("PySide6.QtCore", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)
qtgui = pytest.importorskip("PySide6.QtGui", reason="PySide6 indisponível no ambiente de teste", exc_type=ImportError)

from app import DeleteTeamMembersDialog, TeamSectionTable, selected_members_with_ids

QApplication = qtwidgets.QApplication
QDialog = qtwidgets.QDialog
QTableWidget = qtwidgets.QTableWidget
QTableWidgetItem = qtwidgets.QTableWidgetItem
Qt = qtcore.Qt
QEvent = qtcore.QEvent
QKeyEvent = qtgui.QKeyEvent


def _get_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_selected_members_with_ids_ignores_footer_and_deduplicates_rows():
    _get_app()
    table = QTableWidget(3, 2)
    alice_item = QTableWidgetItem("Alice")
    alice_item.setData(Qt.UserRole, "id-alice")
    table.setItem(0, 0, alice_item)
    table.setItem(0, 1, QTableWidgetItem("K"))

    bob_item = QTableWidgetItem("Bob")
    bob_item.setData(Qt.UserRole, "id-bob")
    table.setItem(1, 0, bob_item)
    table.setItem(1, 1, QTableWidgetItem("P"))

    table.setItem(2, 0, QTableWidgetItem("Participação Dia"))
    table.setItem(2, 1, QTableWidgetItem("2"))

    table.item(0, 1).setSelected(True)
    table.item(0, 0).setSelected(True)
    table.item(1, 1).setSelected(True)
    table.item(2, 0).setSelected(True)

    assert selected_members_with_ids(table) == [("id-alice", "Alice"), ("id-bob", "Bob")]


def test_delete_team_members_dialog_cancel_clears_loaded_members_and_closes_modal():
    _get_app()
    dlg = DeleteTeamMembersDialog(None)
    dlg.show()
    dlg.preload_members([("id-a", "Alice"), ("id-b", "Bob")])

    assert dlg.selected_member_ids() == ["id-a", "id-b"]
    assert dlg.info_label.text() == "Nome(s):\n- Alice\n- Bob"
    assert dlg.confirm_btn.isEnabled()

    dlg._cancel_delete_action()

    assert dlg.result() == QDialog.Rejected
    assert dlg.selected_member_ids() == []
    assert dlg.info_label.text() == ""
    assert not dlg.confirm_btn.isEnabled()
    assert not dlg.isVisible()


def test_team_section_table_delete_key_triggers_handler_for_selected_name_rows_only():
    _get_app()
    table = TeamSectionTable()
    table.setRowCount(3)
    table.setColumnCount(2)

    alice_item = QTableWidgetItem("Alice")
    alice_item.setData(Qt.UserRole, "id-alice")
    table.setItem(0, 0, alice_item)
    table.setItem(0, 1, QTableWidgetItem("K"))
    table.setItem(1, 0, QTableWidgetItem("Bob"))
    table.setItem(2, 0, QTableWidgetItem("Participação Dia"))

    calls = []

    def _delete_handler(_table):
        calls.append(True)
        return True

    table.set_delete_members_handler(_delete_handler)

    table.item(0, 1).setSelected(True)
    table.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier))
    assert calls == []

    table.clearSelection()
    table.item(0, 0).setSelected(True)
    table.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier))
    assert calls == [True]
