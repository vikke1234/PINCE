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
import logging
import re

from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QKeySequence, QTextCursor
from PyQt5.QtWidgets import QWidget, QShortcut, QMessageBox, QMenu
from PyQt5.Qt import QApplication

from application.instance_storage import instances
from application.GUI.ExamineReferrersWidget import Ui_Form as ExamineReferrersWidget
from libPINCE import GuiUtils, GDB_Engine, type_defs, SysUtils


# TODO fix this, currently broken; shelve dictionaries aren't closed when `pince-dissect-code` is called
class ExamineReferrersWidgetForm(QWidget, ExamineReferrersWidget):
    def __init__(self, int_address, parent=None):
        super().__init__()
        self.referrer_data = []
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center_to_parent(self)
        self.setWindowFlags(Qt.Window)
        self.splitter.setStretchFactor(0, 1)
        self.textBrowser_DisasInfo.resize(600, self.textBrowser_DisasInfo.height())
        self.referenced_hex = hex(int_address)
        self.hex_len = 16 if GDB_Engine.inferior_arch == type_defs.INFERIOR_ARCH.ARCH_64 else 8
        self.collect_referrer_data()
        self.refresh_table()
        self.listWidget_Referrers.sortItems(Qt.AscendingOrder)
        self.listWidget_Referrers.selectionModel().currentChanged.connect(self.listWidget_Referrers_current_changed)
        self.listWidget_Referrers.itemDoubleClicked.connect(self.listWidget_Referrers_item_double_clicked)
        self.listWidget_Referrers.contextMenuEvent = self.listWidget_Referrers_context_menu_event
        self.pushButton_Search.clicked.connect(self.refresh_table)
        self.shortcut_search = QShortcut(QKeySequence("Return"), self)
        self.shortcut_search.activated.connect(self.refresh_table)

    def pad_hex(self, hex_str: str) -> str:
        index = hex_str.find(" ")
        if index == -1:
            self_len = 0
        else:
            self_len = len(hex_str) - index
        return '0x{}'.format(hex_str[2:].zfill(self.hex_len + self_len))

    def collect_referrer_data(self) -> None:
        jmp_dict, call_dict = GDB_Engine.get_dissect_code_data(False, True, True)
        self.referrer_data.clear()
        try:
            jmp_referrers = jmp_dict[self.referenced_hex]
        except KeyError:
            pass
        else:
            jmp_referrers = [hex(item) for item in jmp_referrers]
            self.referrer_data.extend([item.all for item in GDB_Engine.examine_expressions(jmp_referrers)])
        try:
            call_referrers = call_dict[self.referenced_hex]
        except KeyError:
            pass
        else:
            call_referrers = [hex(item) for item in call_referrers]
            self.referrer_data.extend([item.all for item in GDB_Engine.examine_expressions(call_referrers)])
        jmp_dict.close()
        call_dict.close()

    def refresh_table(self) -> None:
        searched_str = self.lineEdit_Regex.text()
        case_sensitive = self.checkBox_CaseSensitive.isChecked()
        enable_regex = self.checkBox_Regex.isChecked()
        if enable_regex:
            try:
                if case_sensitive:
                    regex = re.compile(searched_str)
                else:
                    regex = re.compile(searched_str, re.IGNORECASE)
            except re.error:
                logging.exception("Error compiling regex {!r}".format(searched_str))
                QMessageBox.information(self, "Error",
                                        "An exception occurred while trying to compile the given regex\n")
                return
        self.listWidget_Referrers.setSortingEnabled(False)
        self.listWidget_Referrers.clear()
        for row, item in enumerate(self.referrer_data):
            if enable_regex:
                if not regex.search(item):
                    continue
            else:
                if case_sensitive:
                    if item.find(searched_str) == -1:
                        continue
                else:
                    if item.lower().find(searched_str.lower()) == -1:
                        continue
            self.listWidget_Referrers.addItem(item)
        self.listWidget_Referrers.setSortingEnabled(True)
        self.listWidget_Referrers.sortItems(Qt.AscendingOrder)

    def listWidget_Referrers_current_changed(self, QModelIndex_current: QModelIndex) -> None:
        if QModelIndex_current.row() < 0:
            return
        self.textBrowser_DisasInfo.clear()
        disas_data = GDB_Engine.disassemble(
            SysUtils.extract_address(self.listWidget_Referrers.item(QModelIndex_current.row()).text()), "+200")
        for item in disas_data:
            self.textBrowser_DisasInfo.append(item[0] + item[2])
        cursor = self.textBrowser_DisasInfo.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.textBrowser_DisasInfo.setTextCursor(cursor)
        self.textBrowser_DisasInfo.ensureCursorVisible()

    def listWidget_Referrers_item_double_clicked(self, item) -> None:
        self.parent().disassemble_expression(SysUtils.extract_address(item.text()), append_to_travel_history=True)

    def listWidget_Referrers_context_menu_event(self, event) -> None:
        def copy_to_clipboard(row) -> None:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.listWidget_Referrers.item(row).text(), mode=clipboard.Clipboard)

        selected_row = GuiUtils.get_current_row(self.listWidget_Referrers)

        menu = QMenu()
        copy_address = menu.addAction("Copy Address")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [copy_address])
        font_size = self.listWidget_Referrers.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            copy_address: lambda: copy_to_clipboard(selected_row)
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def closeEvent(self, QCloseEvent) -> None:
        instances.remove(self)
