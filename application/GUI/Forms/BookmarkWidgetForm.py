#
#  Copyright (c) 2020 Viktor Horsmanheimo <viktor.horsmanheimo@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget, QShortcut, QMessageBox, QMenu

from application.GUI.Forms.InputDialogForm import InputDialogForm
from application.GUI.BookmarkWidget import Ui_Form as BookmarkWidget
from application.instance_storage import instances
from libPINCE import GuiUtils, GDB_Engine, SysUtils


class BookmarkWidgetForm(QWidget, BookmarkWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center(self)
        self.setWindowFlags(Qt.Window)
        self.listWidget.contextMenuEvent = self.listWidget_context_menu_event
        self.listWidget.currentRowChanged.connect(self.change_display)
        self.listWidget.itemDoubleClicked.connect(self.listWidget_item_double_clicked)
        self.shortcut_delete = QShortcut(QKeySequence("Del"), self)
        self.shortcut_delete.activated.connect(self.delete_record)
        self.shortcut_refresh = QShortcut(QKeySequence("R"), self)
        self.shortcut_refresh.activated.connect(self.refresh_table)
        self.refresh_table()

    def refresh_table(self):
        self.listWidget.clear()
        address_list = [hex(address) for address in self.parent().tableWidget_Disassemble.bookmarks.keys()]
        self.listWidget.addItems([item.all for item in GDB_Engine.examine_expressions(address_list)])

    def change_display(self, row):
        current_address = SysUtils.extract_address(self.listWidget.item(row).text())
        self.lineEdit_Info.setText(GDB_Engine.get_address_info(current_address))
        self.lineEdit_Comment.setText(self.parent().tableWidget_Disassemble.bookmarks[int(current_address, 16)])

    def listWidget_item_double_clicked(self, item):
        self.parent().disassemble_expression(SysUtils.extract_address(item.text()), append_to_travel_history=True)

    def exec_add_entry_dialog(self):
        entry_dialog = InputDialogForm(item_list=[("Enter the expression", "")])
        if entry_dialog.exec_():
            text = entry_dialog.get_values()
            address = GDB_Engine.examine_expression(text).address
            if not address:
                QMessageBox.information(self, "Error", "Invalid expression or address")
                return
            self.parent().bookmark_address(int(address, 16))
            self.refresh_table()

    def exec_change_comment_dialog(self, current_address):
        self.parent().change_bookmark_comment(current_address)
        self.refresh_table()

    def listWidget_context_menu_event(self, event):
        current_item = GuiUtils.get_current_item(self.listWidget)
        if current_item:
            current_address = int(SysUtils.extract_address(current_item.text()), 16)
            if current_address not in self.parent().tableWidget_Disassemble.bookmarks:
                QMessageBox.information(self, "Error", "Invalid entries detected, refreshing the page")
                self.refresh_table()
                return
        else:
            current_address = None
        menu = QMenu()
        add_entry = menu.addAction("Add new entry")
        change_comment = menu.addAction("Change comment of this record")
        delete_record = menu.addAction("Delete this record[Del]")
        if current_item is None:
            GuiUtils.delete_menu_entries(menu, [change_comment, delete_record])
        menu.addSeparator()
        refresh = menu.addAction("Refresh[R]")
        font_size = self.listWidget.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            add_entry: self.exec_add_entry_dialog,
            change_comment: lambda: self.exec_change_comment_dialog(current_address),
            delete_record: self.delete_record,
            refresh: self.refresh_table
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def delete_record(self):
        current_item = GuiUtils.get_current_item(self.listWidget)
        if not current_item:
            return
        current_address = int(SysUtils.extract_address(current_item.text()), 16)
        self.parent().delete_bookmark(current_address)
        self.refresh_table()

    def closeEvent(self, QCloseEvent):

        instances.remove(self)