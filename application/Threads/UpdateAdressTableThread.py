#
#  Copyright (c) 2020 Viktor Horsmanheimo <viktor.horsmanheimo@gmail.com>
#  Copyright (C) 2016-2017 Korcan Karaokçu <korcankaraokcu@gmail.com>
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

from time import sleep

from typing import Tuple
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QTreeWidgetItemIterator, QTreeWidget

from application.constants import ADDR_COL, TYPE_COL, ADDR_EXPR_ROLE
from libPINCE import GuiUtils, GDB_Engine
from application.Settings import table_update_interval

class UpdateAddressTableThread(QThread):
    value_changed = pyqtSignal()

    def __init__(self, treeWidget_AddressTable: QTreeWidget):
        super().__init__()
        self.treeWidget_AddressTable = treeWidget_AddressTable

    # TODO add gdb expressions somehow? https://github.com/korcankaraokcu/PINCE/wiki/About-GDB-Expressions
    # can maybe be placed somehow on the `add address manually` button, idk
    def fetch_new_table_content(self) -> Tuple:
        """
            returns None if there's nothing in the treeWidget_AddressTable

            if it's not empty:
            returns: rows, table_content, new_table_content
            rows: is the rows each of the entries map to
            table_content: the old content to compare to
            new_table_content: the new content (duhh)
        """
        if self.treeWidget_AddressTable is None:
            return None
        it = QTreeWidgetItemIterator(self.treeWidget_AddressTable)
        table_content = []
        address_list = []
        value_type_list = []
        rows = []
        while True:
            row = it.value()
            if not row:
                break
            it += 1
            address_list.append(row.data(ADDR_COL, ADDR_EXPR_ROLE))
            value_type_list.append(row.text(TYPE_COL))
            rows.append(row)
        if len(rows) == 0:
            return None
        for address, value_type in zip(address_list, value_type_list):
            index, length, zero_terminate, byte_len = GuiUtils.text_to_valuetype(value_type)
            table_content.append((address, index, length, zero_terminate))
        new_table_content = GDB_Engine.read_memory_multiple(table_content)
        return rows, table_content, new_table_content

    def run(self):
        # maybe just pass the list to the signal?
        global saved_addresses_changed_list
        while True:
            sleep(table_update_interval)  # this can probably be set from settings?
            ret = self.fetch_new_table_content()
            if ret is None:
                continue
            rows, table_content, new_table_content = ret

            changed_bool = False
            for row, new_val, old_val in zip(rows, new_table_content, table_content):
                if new_val != old_val:
                    saved_addresses_changed_list.append((row, new_val))
                    changed_bool = True
            if changed_bool:
                self.value_changed.emit()