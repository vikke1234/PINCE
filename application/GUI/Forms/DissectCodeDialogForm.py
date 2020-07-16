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
from PyQt5.QtCore import pyqtSignal, QTimer, QThread
from PyQt5.QtWidgets import QDialog, QMessageBox, QTableWidgetItem

from application.GUI.DissectCodeDialog import Ui_Dialog as DissectCodeDialog
from libPINCE import GDB_Engine, SysUtils, type_defs

DISSECT_CODE_ADDR_COL = 0
DISSECT_CODE_PATH_COL = 1


class DissectCodeDialogForm(QDialog, DissectCodeDialog):
    scan_finished_signal = pyqtSignal()

    def __init__(self, parent=None, int_address=-1):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.init_pre_scan_gui()
        self.update_dissect_results()
        self.show_memory_regions()
        self.splitter.setStretchFactor(0, 1)
        self.pushButton_StartCancel.clicked.connect(self.pushButton_StartCancel_clicked)
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(100)
        self.refresh_timer.timeout.connect(self.refresh_dissect_status)
        self.is_scanning = False
        self.is_canceled = False
        if int_address != -1:
            for row in range(self.tableWidget_ExecutableMemoryRegions.rowCount()):
                item = self.tableWidget_ExecutableMemoryRegions.item(row, DISSECT_CODE_ADDR_COL).text()
                start_addr, end_addr = item.split("-")
                if int(start_addr, 16) <= int_address <= int(end_addr, 16):
                    self.tableWidget_ExecutableMemoryRegions.clearSelection()
                    self.tableWidget_ExecutableMemoryRegions.selectRow(row)
                    self.pushButton_StartCancel_clicked()
                    break
            else:
                QMessageBox.information(self, "Error", hex(int_address) + " isn't in a valid region range")
        else:
            if self.tableWidget_ExecutableMemoryRegions.rowCount() > 0:
                self.tableWidget_ExecutableMemoryRegions.selectRow(0)

    class BackgroundThread(QThread):
        output_ready = pyqtSignal()
        is_canceled = False

        def __init__(self, region_list, discard_invalid_strings):
            super().__init__()
            self.region_list = region_list
            self.discard_invalid_strings = discard_invalid_strings

        def run(self):
            GDB_Engine.dissect_code(self.region_list, self.discard_invalid_strings)
            if not self.is_canceled:
                self.output_ready.emit()

    def init_pre_scan_gui(self):
        self.is_scanning = False
        self.is_canceled = False
        self.pushButton_StartCancel.setText("Start")

    def init_after_scan_gui(self):
        self.is_scanning = True
        self.label_ScanInfo.setText("Currently scanning region:")
        self.pushButton_StartCancel.setText("Cancel")

    def refresh_dissect_status(self):
        region, region_count, region_range, string_count, jump_count, call_count = GDB_Engine.get_dissect_code_status()
        if not region:
            return
        self.label_RegionInfo.setText(region)
        self.label_RegionCountInfo.setText(region_count)
        self.label_CurrentRange.setText(region_range)
        self.label_StringReferenceCount.setText(str(string_count))
        self.label_JumpReferenceCount.setText(str(jump_count))
        self.label_CallReferenceCount.setText(str(call_count))

    def update_dissect_results(self):
        try:
            referenced_strings, referenced_jumps, referenced_calls = GDB_Engine.get_dissect_code_data()
        except:
            logging.exception("error updating dissect results")
            return
        self.label_StringReferenceCount.setText(str(len(referenced_strings)))
        self.label_JumpReferenceCount.setText(str(len(referenced_jumps)))
        self.label_CallReferenceCount.setText(str(len(referenced_calls)))

    def show_memory_regions(self):
        executable_regions = SysUtils.filter_memory_regions(GDB_Engine.currentpid, "perms", "..x.")
        self.region_list = executable_regions
        self.tableWidget_ExecutableMemoryRegions.setRowCount(0)
        self.tableWidget_ExecutableMemoryRegions.setRowCount(len(executable_regions))
        for row, region in enumerate(executable_regions):
            self.tableWidget_ExecutableMemoryRegions.setItem(row, DISSECT_CODE_ADDR_COL, QTableWidgetItem(region.addr))
            self.tableWidget_ExecutableMemoryRegions.setItem(row, DISSECT_CODE_PATH_COL, QTableWidgetItem(region.path))
        self.tableWidget_ExecutableMemoryRegions.resizeColumnsToContents()
        self.tableWidget_ExecutableMemoryRegions.horizontalHeader().setStretchLastSection(True)

    def scan_finished(self):
        self.init_pre_scan_gui()
        if not self.is_canceled:
            self.label_ScanInfo.setText("Scan finished")
        self.is_canceled = False
        self.refresh_timer.stop()
        self.refresh_dissect_status()
        self.update_dissect_results()
        self.scan_finished_signal.emit()

    def pushButton_StartCancel_clicked(self):
        if self.is_scanning:
            self.is_canceled = True
            self.background_thread.is_canceled = True
            GDB_Engine.cancel_dissect_code()
            self.refresh_timer.stop()
            self.update_dissect_results()
            self.label_ScanInfo.setText("Scan was canceled")
            self.init_pre_scan_gui()
        else:
            if not GDB_Engine.inferior_status == type_defs.INFERIOR_STATUS.INFERIOR_STOPPED:
                QMessageBox.information(self, "Error", "Please stop the process first")
                return
            selected_rows = self.tableWidget_ExecutableMemoryRegions.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.information(self, "Error", "Select at least one region")
                return
            selected_indexes = [selected_row.row() for selected_row in selected_rows]
            selected_regions = [self.region_list[selected_index] for selected_index in selected_indexes]
            self.background_thread = self.BackgroundThread(selected_regions,
                                                           self.checkBox_DiscardInvalidStrings.isChecked())
            self.background_thread.output_ready.connect(self.scan_finished)
            self.init_after_scan_gui()
            self.refresh_timer.start()
            self.background_thread.start()

    def closeEvent(self, QCloseEvent):
        GDB_Engine.cancel_dissect_code()
        self.refresh_timer.stop()
