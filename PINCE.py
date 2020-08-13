#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2016-2017 Korcan Karaokçu <korcankaraokcu@gmail.com>
Copyright (C) 2016-2017 Çağrı Ulaş <cagriulas@gmail.com>
Copyright (C) 2016-2017 Jakob Kreuze <jakob@memeware.net>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import ast
import collections
import copy
import io
import os
import re
import signal
import sys
import traceback
import logging
import getopt
from time import sleep, time
from typing import List
import psutil
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QByteArray, QSettings, QEvent, \
    QItemSelectionModel, QTimer, QModelIndex, QRegExp
from PyQt5.QtGui import QIcon, QMovie, QPixmap, QKeySequence, QColor, QTextCharFormat, QBrush, QTextCursor, \
    QRegExpValidator
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QDialog, QWidget, \
    QShortcut, QKeySequenceEdit, QTabWidget, QMenu, QFileDialog, QAbstractItemView, QTreeWidgetItem, \
    QTreeWidgetItemIterator, QDialogButtonBox

import application.Settings
from application import Hotkeys
from application.GUI.Forms.AboutWidgetForm import AboutWidgetForm
from application.GUI.Forms.BookmarkWidgetForm import BookmarkWidgetForm
from application.GUI.Forms.ConsoleWidgetForm import ConsoleWidgetForm
from application.GUI.Forms.EditTypeDialogForm import EditTypeDialogForm
from application.GUI.Forms.InputDialogForm import InputDialogForm
from application.GUI.Forms.LoadingDialogForm import LoadingDialogForm
from application.GUI.Forms.ManualAddressDialogForm import ManualAddressDialogForm
from application.GUI.Forms.ProcessForm import ProcessForm
from application.instance_storage import instances
from application.CheckInferiorStatus import CheckInferiorStatus
from application.GUI.BreakpointInfoWidget import Ui_TabWidget as BreakpointInfoWidget
from application.GUI.CustomAbstractTableModels.AsciiModel import QAsciiModel
from application.GUI.CustomAbstractTableModels.HexModel import QHexModel
from application.GUI.CustomValidators.HexValidator import QHexValidator
from application.GUI.ExamineReferrersWidget import Ui_Form as ExamineReferrersWidget
from application.GUI.FloatRegisterWidget import Ui_TabWidget as FloatRegisterWidget
from application.GUI.Forms.DissectCodeDialogForm import DissectCodeDialogForm
from application.GUI.FunctionsInfoWidget import Ui_Form as FunctionsInfoWidget
from application.GUI.HexEditDialog import Ui_Dialog as HexEditDialog
from application.GUI.LibPINCEReferenceWidget import Ui_Form as LibPINCEReferenceWidget
from application.GUI.LogFileWidget import Ui_Form as LogFileWidget
from application.GUI.MainWindow import Ui_MainWindow as MainWindow
from application.GUI.MemoryRegionsWidget import Ui_Form as MemoryRegionsWidget
# If you are going to change the name "Ui_MainWindow_MemoryView", review GUI/CustomLabels/RegisterLabel.py as well
from application.GUI.MemoryViewerWindow import Ui_MainWindow_MemoryView as MemoryViewWindow
from application.GUI.ReferencedCallsWidget import Ui_Form as ReferencedCallsWidget
from application.GUI.ReferencedStringsWidget import Ui_Form as ReferencedStringsWidget
from application.GUI.SearchOpcodeWidget import Ui_Form as SearchOpcodeWidget
from application.GUI.SettingsDialog import Ui_Dialog as SettingsDialog
from application.GUI.StackTraceInfoWidget import Ui_Form as StackTraceInfoWidget
from application.GUI.TraceInstructionsPromptDialog import Ui_Dialog as TraceInstructionsPromptDialog
from application.GUI.TraceInstructionsWaitWidget import Ui_Form as TraceInstructionsWaitWidget
from application.GUI.TraceInstructionsWindow import Ui_MainWindow as TraceInstructionsWindow
from application.GUI.TrackBreakpointWidget import Ui_Form as TrackBreakpointWidget
from application.GUI.TrackWatchpointWidget import Ui_Form as TrackWatchpointWidget
from application.Settings import Break, current_settings_version, show_messagebox_on_exception, \
    show_messagebox_on_toggle_attach, auto_attach_list, auto_attach_regex, bring_disassemble_to_front, \
    instructions_per_scroll, gdb_path, gdb_logging, DISAS_ADDR_COL, \
    DISAS_BYTES_COL, DISAS_OPCODES_COL, DISAS_COMMENT_COL, FLOAT_REGISTERS_NAME_COL, FLOAT_REGISTERS_VALUE_COL, \
    STACKTRACE_RETURN_ADDRESS_COL, STACKTRACE_FRAME_ADDRESS_COL, STACK_POINTER_ADDRESS_COL, STACK_VALUE_COL, \
    STACK_POINTS_TO_COL, HEX_VIEW_COL_COUNT, HEX_VIEW_ROW_COUNT, TRACK_WATCHPOINT_COUNT_COL, TRACK_WATCHPOINT_ADDR_COL, \
    TRACK_BREAKPOINT_COUNT_COL, TRACK_BREAKPOINT_ADDR_COL, TRACK_BREAKPOINT_VALUE_COL, TRACK_BREAKPOINT_SOURCE_COL, \
    FUNCTIONS_INFO_ADDR_COL, FUNCTIONS_INFO_SYMBOL_COL, LIBPINCE_REFERENCE_ITEM_COL, LIBPINCE_REFERENCE_VALUE_COL, \
    SEARCH_OPCODE_ADDR_COL, SEARCH_OPCODE_OPCODES_COL, MEMORY_REGIONS_ADDR_COL, MEMORY_REGIONS_PERM_COL, \
    MEMORY_REGIONS_SIZE_COL, MEMORY_REGIONS_PATH_COL, MEMORY_REGIONS_RSS_COL, MEMORY_REGIONS_PSS_COL, \
    MEMORY_REGIONS_SHRCLN_COL, MEMORY_REGIONS_SHRDRTY_COL, MEMORY_REGIONS_PRIVCLN_COL, MEMORY_REGIONS_PRIVDRTY_COL, \
    MEMORY_REGIONS_REF_COL, MEMORY_REGIONS_ANON_COL, MEMORY_REGIONS_SWAP_COL, REF_STR_ADDR_COL, REF_STR_COUNT_COL, REF_STR_VAL_COL, REF_CALL_ADDR_COL, REF_CALL_COUNT_COL
from application.Threads.AwaitProcessExitThread import AwaitProcessExit
from application.Threads.UpdateAdressTableThread import UpdateAddressTableThread
from application.constants import PC_COLOUR, BOOKMARK_COLOUR, FROZEN_COL, VALUE_COL, ADDR_COL, DESC_COL, REF_COLOUR, \
    TYPE_COL, ADDR_EXPR_ROLE, BREAKPOINT_COLOUR
from libPINCE import GuiUtils, SysUtils, GDB_Engine, type_defs
from libPINCE.libscanmem.scanmem import Scanmem


# used for automatically updating the values in the saved address tree widget
# see UpdateAddressTableThread
saved_addresses_changed_list:List = []

def except_hook(exception_type, value, tb):
    if show_messagebox_on_exception:
        focused_widget = app.focusWidget()
        if focused_widget:
            if exception_type == type_defs.GDBInitializeException:
                QMessageBox.information(focused_widget, "Error", "GDB isn't initialized yet")
            elif exception_type == type_defs.InferiorRunningException:
                error_dialog = InputDialogForm(item_list=[(
                    "Process is running" + "\nPress " + Hotkeys.break_hotkey.value + " to stop process" +
                    "\n\nGo to Settings->General to disable this dialog",)], buttons=[QDialogButtonBox.Ok])
                error_dialog.exec_()
    traceback.print_exception(exception_type, value, tb)


# From version 5.5 and onwards, PyQT calls qFatal() when an exception has been encountered
# So, we must override sys.excepthook to avoid calling of qFatal()
sys.excepthook = except_hook


def signal_handler(signal, frame):
    GDB_Engine.cancel_last_command()
    raise KeyboardInterrupt


signal.signal(signal.SIGINT, signal_handler)


# Checks if the inferior has been terminated


class MainForm(QMainWindow, MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.hotkey_to_shortcut = {}  # Dict[str:QShortcut]-->Dict[Hotkey.name:QShortcut(QKeySequence(Hotkey.value)]
        hotkey_to_func = {
            Hotkeys.pause_hotkey: self.pause_hotkey_pressed,
            Hotkeys.break_hotkey: self.break_hotkey_pressed,
            Hotkeys.continue_hotkey: self.continue_hotkey_pressed,
            Hotkeys.toggle_attach_hotkey: self.toggle_attach_hotkey_pressed
        }
        for hotkey, func in hotkey_to_func.items():
            current_shortcut = QShortcut(QKeySequence(hotkey.value), self)
            current_shortcut.activated.connect(func)
            current_shortcut.setContext(hotkey.context)
            self.hotkey_to_shortcut[hotkey.name] = current_shortcut
        GuiUtils.center(self)
        self.treeWidget_AddressTable.setColumnWidth(FROZEN_COL, 50)
        self.treeWidget_AddressTable.setColumnWidth(DESC_COL, 150)
        self.treeWidget_AddressTable.setColumnWidth(ADDR_COL, 150)
        self.treeWidget_AddressTable.setColumnWidth(TYPE_COL, 150)
        app.setOrganizationName("PINCE")
        app.setOrganizationDomain("github.com/korcankaraokcu/PINCE")
        app.setApplicationName("PINCE")
        QSettings.setPath(QSettings.NativeFormat, QSettings.UserScope,
                          SysUtils.get_user_path(type_defs.USER_PATHS.CONFIG_PATH))
        self.settings = QSettings()
        if not SysUtils.is_path_valid(self.settings.fileName()):
            self.set_default_settings()
        try:
            settings_version = self.settings.value("Misc/version", type=str)
        except Exception as e:
            logging.exception("An exception occurred while reading settings version")
            settings_version = None
        if settings_version != current_settings_version:
            logging.warning("Settings version mismatch, rolling back to the default configuration")
            self.settings.clear()
            self.set_default_settings()
        try:
            self.apply_settings()
        except Exception as e:
            logging.exception("An exception occurred while trying to load settings, "
                              "rolling back to the default configuration")
            self.settings.clear()
            self.set_default_settings()
        logging.debug("gdb_path: {}".format(gdb_path))
        GDB_Engine.init_gdb(gdb_path=gdb_path)
        GDB_Engine.set_logging(gdb_logging)
        # this should be changed, only works if you use the current directory,
        # fails if you for example install it to some place like bin
        libscanmem_path = os.path.join(os.getcwd(), "libPINCE", "libscanmem", "libscanmem.so")
        self.backend = Scanmem(libscanmem_path)
        self.backend.send_command("option noptrace 1")
        self.memory_view_window = MemoryViewWindowForm(self)
        self.about_widget = AboutWidgetForm()
        self.await_exit_thread = AwaitProcessExit()
        self.await_exit_thread.process_exited.connect(self.on_inferior_exit)
        self.await_exit_thread.start()
        self.check_status_thread = CheckInferiorStatus()
        self.check_status_thread.process_stopped.connect(self.on_status_stopped)
        self.check_status_thread.process_running.connect(self.on_status_running)
        self.check_status_thread.process_stopped.connect(self.memory_view_window.process_stopped)
        self.check_status_thread.process_running.connect(self.memory_view_window.process_running)
        self.check_status_thread.start()
        self.update_address_table_thread = UpdateAddressTableThread(self.treeWidget_AddressTable)
        self.update_address_table_thread.value_changed.connect(self.update_address_table_automatically)
        self.update_address_table_thread.start()
        self.shortcut_open_file = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut_open_file.activated.connect(self.pushButton_Open_clicked)
        GuiUtils.append_shortcut_to_tooltip(self.pushButton_Open, self.shortcut_open_file)
        self.shortcut_save_file = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save_file.activated.connect(self.pushButton_Save_clicked)
        GuiUtils.append_shortcut_to_tooltip(self.pushButton_Save, self.shortcut_save_file)
        # Saving the original function because super() doesn't work when we override functions like this
        self.treeWidget_AddressTable.keyPressEvent_original = self.treeWidget_AddressTable.keyPressEvent
        self.treeWidget_AddressTable.keyPressEvent = self.treeWidget_AddressTable_key_press_event
        self.treeWidget_AddressTable.contextMenuEvent = self.treeWidget_AddressTable_context_menu_event
        self.pushButton_AttachProcess.clicked.connect(self.pushButton_AttachProcess_clicked)
        self.pushButton_Open.clicked.connect(self.pushButton_Open_clicked)
        self.pushButton_Save.clicked.connect(self.pushButton_Save_clicked)
        self.pushButton_NewFirstScan.clicked.connect(self.pushButton_NewFirstScan_clicked)
        self.pushButton_NextScan.clicked.connect(self.pushButton_NextScan_clicked)
        self.pushButton_NextScan.setEnabled(False)
        self.checkBox_Hex.stateChanged.connect(self.checkBox_Hex_stateChanged)
        self.comboBox_ValueType.currentTextChanged.connect(self.comboBox_ValueType_textChanged)
        self.lineEdit_Scan.setValidator(QRegExpValidator(QRegExp("-?[0-9]*"), parent=self.lineEdit_Scan))
        self.comboBox_ScanType.addItems(
            ["Exact Match", "Increased", "Decreased", "Less Than", "More than", "Changed", "Unchanged"])
        self.pushButton_Settings.clicked.connect(self.pushButton_Settings_clicked)
        self.pushButton_Console.clicked.connect(self.pushButton_Console_clicked)
        self.pushButton_Wiki.clicked.connect(self.pushButton_Wiki_clicked)
        self.pushButton_About.clicked.connect(self.pushButton_About_clicked)
        self.pushButton_AddAddressManually.clicked.connect(self.pushButton_AddAddressManually_clicked)
        self.pushButton_MemoryView.clicked.connect(self.pushButton_MemoryView_clicked)
        self.pushButton_RefreshAdressTable.clicked.connect(self.update_address_table_manually)
        self.pushButton_CleanAddressTable.clicked.connect(self.delete_address_table_contents)
        self.tableWidget_valuesearchtable.cellDoubleClicked.connect(
            self.tableWidget_valuesearchtable_cell_double_clicked)
        self.treeWidget_AddressTable.itemDoubleClicked.connect(self.treeWidget_AddressTable_item_double_clicked)
        self.treeWidget_AddressTable.expanded.connect(self.resize_address_table)
        self.treeWidget_AddressTable.collapsed.connect(self.resize_address_table)
        icons_directory = GuiUtils.get_icons_directory()
        current_dir = SysUtils.get_current_script_directory()
        self.pushButton_AttachProcess.setIcon(QIcon(QPixmap(icons_directory + "/monitor.png")))
        self.pushButton_Open.setIcon(QIcon(QPixmap(icons_directory + "/folder.png")))
        self.pushButton_Save.setIcon(QIcon(QPixmap(icons_directory + "/disk.png")))
        self.pushButton_Settings.setIcon(QIcon(QPixmap(icons_directory + "/wrench.png")))
        self.pushButton_CopyToAddressTable.setIcon(QIcon(QPixmap(icons_directory + "/arrow_down.png")))
        self.pushButton_CleanAddressTable.setIcon(QIcon(QPixmap(icons_directory + "/bin_closed.png")))
        self.pushButton_RefreshAdressTable.setIcon(QIcon(QPixmap(icons_directory + "/table_refresh.png")))
        self.pushButton_Console.setIcon(QIcon(QPixmap(icons_directory + "/application_xp_terminal.png")))
        self.pushButton_Wiki.setIcon(QIcon(QPixmap(icons_directory + "/book_open.png")))
        self.pushButton_About.setIcon(QIcon(QPixmap(icons_directory + "/information.png")))
        self.auto_attach()

    def set_default_settings(self):
        self.settings.beginGroup("General")
        self.settings.setValue("update_table", True)  # uh kinda not used right now
        self.settings.setValue("address_table_update_interval", 0.2)
        self.settings.setValue("show_messagebox_on_exception", True)
        self.settings.setValue("show_messagebox_on_toggle_attach", True)
        self.settings.setValue("gdb_output_mode", type_defs.gdb_output_mode(True, True, True))
        self.settings.setValue("auto_attach_list", "")
        self.settings.setValue("logo_path", "ozgurozbek/pince_small_transparent.png")
        self.settings.setValue("auto_attach_regex", False)
        self.settings.endGroup()
        self.settings.beginGroup("Hotkeys")
        for hotkey in Hotkeys.Hotkey.get_hotkeys():
            self.settings.setValue(hotkey.name, hotkey.default)
        self.settings.endGroup()
        self.settings.beginGroup("CodeInjection")
        self.settings.setValue("code_injection_method", type_defs.INJECTION_METHOD.SIMPLE_DLOPEN_CALL)
        self.settings.endGroup()
        self.settings.beginGroup("Disassemble")
        self.settings.setValue("bring_disassemble_to_front", False)
        self.settings.setValue("instructions_per_scroll", 2)
        self.settings.endGroup()
        self.settings.beginGroup("Debug")
        self.settings.setValue("gdb_path", type_defs.PATHS.GDB_PATH)
        self.settings.setValue("gdb_logging", False)
        self.settings.endGroup()
        self.settings.beginGroup("Misc")
        self.settings.setValue("version", current_settings_version)
        self.settings.endGroup()
        self.apply_settings()

    def apply_settings(self):
        application.Settings.update_table = self.settings.value("General/auto_update_address_table", type=bool)
        application.Settings.table_update_interval = self.settings.value("General/address_table_update_interval",
                                                                         type=float)
        application.Settings.show_messagebox_on_exception = self.settings.value("General/show_messagebox_on_exception",
                                                                                type=bool)
        application.Settings.show_messagebox_on_toggle_attach = self.settings.value(
            "General/show_messagebox_on_toggle_attach", type=bool)
        application.Settings.gdb_output_mode = self.settings.value("General/gdb_output_mode", type=tuple)
        application.Settings.auto_attach_list = self.settings.value("General/auto_attach_list", type=str)
        application.Settings.logo_path = self.settings.value("General/logo_path", type=str)
        app.setWindowIcon(QIcon(os.path.join(SysUtils.get_logo_directory(), application.Settings.logo_path)))
        application.Settings.auto_attach_regex = self.settings.value("General/auto_attach_regex", type=bool)
        GDB_Engine.set_gdb_output_mode(application.Settings.gdb_output_mode)
        for hotkey in Hotkeys.Hotkey.get_hotkeys():
            hotkey.value = self.settings.value("Hotkeys/" + hotkey.name)
            self.hotkey_to_shortcut[hotkey.name].setKey(QKeySequence(hotkey.value))
        try:
            self.memory_view_window.set_dynamic_debug_hotkeys()
        except AttributeError:
            pass
        application.Settings.code_injection_method = self.settings.value("CodeInjection/code_injection_method",
                                                                         type=int)
        application.Settings.bring_disassemble_to_front = self.settings.value("Disassemble/bring_disassemble_to_front",
                                                                              type=bool)
        application.Settings.instructions_per_scroll = self.settings.value("Disassemble/instructions_per_scroll",
                                                                           type=int)
        application.Settings.gdb_path = self.settings.value("Debug/gdb_path", type=str)
        application.Settings.gdb_logging = self.settings.value("Debug/gdb_logging", type=bool)
        if GDB_Engine.gdb_initialized:
            GDB_Engine.set_logging(application.Settings.gdb_logging)

    # Check if any process should be attached to automatically
    # Patterns at former positions have higher priority if regex is off
    def auto_attach(self):
        logging.info("auto attach list: {}".format(auto_attach_list))
        if not auto_attach_list:
            return
        if auto_attach_regex:
            try:
                compiled_re = re.compile(auto_attach_list)
            except re.error as e:
                logging.exception("Could not compile regex: {!r}".format(auto_attach_list))
                return
            for process in SysUtils.iterate_processes():
                try:
                    name = process.name()
                except psutil.NoSuchProcess:
                    logging.error("could not find process: {}".format(process))
                    continue
                if compiled_re.search(name):
                    self.attach_to_pid(process.pid)
                    return
        else:
            for target in auto_attach_list.split(";"):
                for process in SysUtils.iterate_processes():
                    try:
                        name = process.name()
                    except psutil.NoSuchProcess:
                        logging.error("could not find process: {}".format(process))
                        continue
                    if name.find(target) != -1:
                        self.attach_to_pid(process.pid)
                        return

    def pause_hotkey_pressed(self):
        GDB_Engine.interrupt_inferior(type_defs.STOP_REASON.PAUSE)

    def break_hotkey_pressed(self):
        GDB_Engine.interrupt_inferior()

    def continue_hotkey_pressed(self):
        GDB_Engine.continue_inferior()

    def toggle_attach_hotkey_pressed(self):
        result = GDB_Engine.toggle_attach()
        if not result:
            dialog_text = "Unable to toggle attach"
        elif result == type_defs.TOGGLE_ATTACH.DETACHED:
            self.on_status_detached()
            dialog_text = "GDB is detached from the process"
        else:
            dialog_text = "GDB is attached back to the process"
        if show_messagebox_on_toggle_attach:
            dialog = InputDialogForm(item_list=[(
                dialog_text + "\n\nGo to Settings->General to disable this dialog",)], buttons=[QDialogButtonBox.Ok])
            dialog.exec_()

    def treeWidget_AddressTable_context_menu_event(self, event):
        current_row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        menu = QMenu()
        edit_menu = menu.addMenu("Edit")
        edit_desc = edit_menu.addAction("Description[Ctrl+Enter]")
        edit_address = edit_menu.addAction("Address[Ctrl+Alt+Enter]")
        edit_type = edit_menu.addAction("Type[Alt+Enter]")
        edit_value = edit_menu.addAction("Value[Enter]")
        # TODO: Implement toggling of records
        toggle_record = menu.addAction("Toggle selected records[Space] (not implemented yet)")
        menu.addSeparator()
        browse_region = menu.addAction("Browse this memory region[Ctrl+B]")
        disassemble = menu.addAction("Disassemble this address[Ctrl+D]")
        menu.addSeparator()
        cut_record = menu.addAction("Cut selected records[Ctrl+X]")
        copy_record = menu.addAction("Copy selected records[Ctrl+C]")
        cut_record_recursively = menu.addAction("Cut selected records (recursive)[X]")
        copy_record_recursively = menu.addAction("Copy selected records (recursive)[C]")
        paste_record_before = menu.addAction("Paste selected records before[Ctrl+V]")
        paste_record_after = menu.addAction("Paste selected records after[V]")
        paste_record_inside = menu.addAction("Paste selected records inside[I]")
        delete_record = menu.addAction("Delete selected records[Del]")
        menu.addSeparator()
        what_writes = menu.addAction("Find out what writes to this address")
        what_reads = menu.addAction("Find out what reads this address")
        what_accesses = menu.addAction("Find out what accesses this address")
        if current_row is None:
            deletion_list = [edit_menu.menuAction(), toggle_record, browse_region, disassemble, what_writes, what_reads,
                             what_accesses]
            GuiUtils.delete_menu_entries(menu, deletion_list)
        font_size = self.treeWidget_AddressTable.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            edit_desc: self.treeWidget_AddressTable_edit_desc,
            edit_address: self.treeWidget_AddressTable_edit_address,
            edit_type: self.treeWidget_AddressTable_edit_type,
            edit_value: self.treeWidget_AddressTable_edit_value,
            toggle_record: self.toggle_selected_records,
            browse_region: self.browse_region_for_selected_row,
            disassemble: self.disassemble_selected_row,
            cut_record: self.cut_selected_records,
            copy_record: self.copy_selected_records,
            cut_record_recursively: self.cut_selected_records_recursively,
            copy_record_recursively: self.copy_selected_records_recursively,
            paste_record_before: lambda: self.paste_records(insert_after=False),
            paste_record_after: lambda: self.paste_records(insert_after=True),
            paste_record_inside: lambda: self.paste_records(insert_inside=True),
            delete_record: self.delete_selected_records,
            what_writes: lambda: self.exec_track_watchpoint_widget(type_defs.WATCHPOINT_TYPE.WRITE_ONLY),
            what_reads: lambda: self.exec_track_watchpoint_widget(type_defs.WATCHPOINT_TYPE.READ_ONLY),
            what_accesses: lambda: self.exec_track_watchpoint_widget(type_defs.WATCHPOINT_TYPE.BOTH)
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def exec_track_watchpoint_widget(self, watchpoint_type):
        selected_row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        if not selected_row:
            return
        address = selected_row.text(ADDR_COL)
        value_type_text = selected_row.text(TYPE_COL)
        index, length, zero_terminate, byte_len = GuiUtils.text_to_valuetype(value_type_text)
        if byte_len == -1:
            value_text = selected_row.text(VALUE_COL)
            encoding, option = type_defs.string_index_to_encoding_dict[index]
            byte_len = len(value_text.encode(encoding, option))
        TrackWatchpointWidgetForm(address, byte_len, watchpoint_type, self).show()

    def browse_region_for_selected_row(self):
        row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        if row:
            self.memory_view_window.hex_dump_address(int(row.text(ADDR_COL), 16))
            self.memory_view_window.show()
            self.memory_view_window.activateWindow()

    def disassemble_selected_row(self):
        row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        if row:
            if self.memory_view_window.disassemble_expression(row.text(ADDR_COL), append_to_travel_history=True):
                self.memory_view_window.show()
                self.memory_view_window.activateWindow()

    def toggle_selected_records(self):
        row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        if row:
            check_state = row.checkState(FROZEN_COL)
            new_check_state = Qt.Checked if check_state == Qt.Unchecked else Qt.Unchecked
            for row in self.treeWidget_AddressTable.selectedItems():
                row.setCheckState(FROZEN_COL, new_check_state)

    def cut_selected_records(self):
        # Flat cut, does not preserve structure
        self.copy_selected_records()
        self.delete_selected_records()

    def copy_selected_records(self):
        # Flat copy, does not preserve structure
        app.clipboard().setText(repr([self.read_address_table_entries(selected_row) + ((),) for selected_row in
                                      self.treeWidget_AddressTable.selectedItems()]))
        # each element in the list has no children

    def cut_selected_records_recursively(self):
        self.copy_selected_records_recursively()
        self.delete_selected_records()

    def copy_selected_records_recursively(self):
        # Recursive copy
        items = self.treeWidget_AddressTable.selectedItems()

        def index_of(item):
            """Returns the index used to access the given QTreeWidgetItem
            as a list of ints."""
            result = []
            while True:
                parent = item.parent()
                if parent:
                    result.append(parent.indexOfChild(item))
                    item = parent
                else:
                    result.append(item.treeWidget().indexOfTopLevelItem(item))
                    return result[::-1]

        # First, order the items by their indices in the tree widget.
        # Store the indices for later usage.
        index_items = [(index_of(item), item) for item in items]
        index_items.sort(key=lambda x: x[0])  # sort by index

        # Now filter any selected items that is a descendant of another selected items.
        items = []
        last_index = [-1]  # any invalid list of indices are fine
        for index, item in index_items:
            if index[:len(last_index)] == last_index:
                continue  # this item is a descendant of the last item
            items.append(item)
            last_index = index

        app.clipboard().setText(repr([self.read_address_table_recursively(item) for item in items]))

    def insert_records(self, records, parent_row, insert_index):
        # parent_row should be a QTreeWidgetItem in treeWidget_AddressTable
        # records should be an iterable of valid output of read_address_table_recursively
        assert isinstance(parent_row, QTreeWidgetItem)

        rows = []
        for rec in records:
            row = QTreeWidgetItem()
            row.setCheckState(FROZEN_COL, Qt.Unchecked)
            self.change_address_table_entries(row, *rec[:-1])
            self.insert_records(rec[-1], row, 0)
            rows.append(row)

        parent_row.insertChildren(insert_index, rows)

    def paste_records(self, insert_after=None, insert_inside=False):
        try:
            records = ast.literal_eval(app.clipboard().text())
        except (SyntaxError, ValueError):
            QMessageBox.information(self, "Error", "Invalid clipboard content")
            return

        insert_row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        root = self.treeWidget_AddressTable.invisibleRootItem()
        if not insert_row:  # this is common when the treeWidget_AddressTable is empty
            self.insert_records(records, root, self.treeWidget_AddressTable.topLevelItemCount())
        elif insert_inside:
            self.insert_records(records, insert_row, 0)
        else:
            parent = insert_row.parent() or root
            self.insert_records(records, parent, parent.indexOfChild(insert_row) + insert_after)
        self.update_address_table_manually()

    def delete_selected_records(self):
        root = self.treeWidget_AddressTable.invisibleRootItem()
        for item in self.treeWidget_AddressTable.selectedItems():
            (item.parent() or root).removeChild(item)

    def treeWidget_AddressTable_key_press_event(self, event):
        actions = type_defs.KeyboardModifiersTupleDict([
            ((Qt.NoModifier, Qt.Key_Delete), self.delete_selected_records),
            ((Qt.ControlModifier, Qt.Key_B), self.browse_region_for_selected_row),
            ((Qt.ControlModifier, Qt.Key_D), self.disassemble_selected_row),
            ((Qt.NoModifier, Qt.Key_R), self.update_address_table_manually),
            ((Qt.NoModifier, Qt.Key_Space), self.toggle_selected_records),
            ((Qt.ControlModifier, Qt.Key_X), self.cut_selected_records),
            ((Qt.ControlModifier, Qt.Key_C), self.copy_selected_records),
            ((Qt.NoModifier, Qt.Key_X), self.cut_selected_records_recursively),
            ((Qt.NoModifier, Qt.Key_C), self.copy_selected_records_recursively),
            ((Qt.ControlModifier, Qt.Key_V), lambda: self.paste_records(insert_after=False)),
            ((Qt.NoModifier, Qt.Key_V), lambda: self.paste_records(insert_after=True)),
            ((Qt.NoModifier, Qt.Key_I), lambda: self.paste_records(insert_inside=True)),
            ((Qt.NoModifier, Qt.Key_Return), self.treeWidget_AddressTable_edit_value),
            ((Qt.ControlModifier, Qt.Key_Return), self.treeWidget_AddressTable_edit_desc),
            ((Qt.ControlModifier | Qt.AltModifier, Qt.Key_Return), self.treeWidget_AddressTable_edit_address),
            ((Qt.AltModifier, Qt.Key_Return), self.treeWidget_AddressTable_edit_type)
        ])
        try:
            actions[event.modifiers(), event.key()]()
        except KeyError:
            self.treeWidget_AddressTable.keyPressEvent_original(event)

    def update_address_table_automatically(self, saved_addresses_changed_list):
        for row, value in saved_addresses_changed_list:
            row.setText(VALUE_COL, str(value))

        saved_addresses_changed_list = []  # not sure which is faster, clearing or just setting a new one

    def update_address_table_manually(self):
        it = QTreeWidgetItemIterator(self.treeWidget_AddressTable)
        table_contents = []
        address_expr_list = []
        value_type_list = []
        rows = []
        while True:
            row = it.value()
            if not row:
                break
            it += 1
            address_expr_list.append(row.data(ADDR_COL, ADDR_EXPR_ROLE))
            value_type_list.append(row.text(TYPE_COL))
            rows.append(row)
        address_list = [item.address for item in GDB_Engine.examine_expressions(address_expr_list)]
        for address, value_type in zip(address_list, value_type_list):
            index, length, zero_terminate, byte_len = GuiUtils.text_to_valuetype(value_type)
            table_contents.append((address, index, length, zero_terminate))
        new_table_contents = GDB_Engine.read_memory_multiple(table_contents)
        for row, address, address_expr, value in zip(rows, address_list, address_expr_list, new_table_contents):
            row.setText(ADDR_COL, address or address_expr)
            row.setText(VALUE_COL, "" if value is None else str(value))

    def resize_address_table(self):
        self.treeWidget_AddressTable.resizeColumnToContents(FROZEN_COL)

    # gets the information from the dialog then adds it to addresstable
    def pushButton_AddAddressManually_clicked(self):
        manual_address_dialog = ManualAddressDialogForm()
        if manual_address_dialog.exec_():
            description, address_expr, address_type, length, zero_terminate = manual_address_dialog.get_values()
            self.add_entry_to_addresstable(description, address_expr, address_type, length, zero_terminate)

    def pushButton_MemoryView_clicked(self):
        self.memory_view_window.showMaximized()
        self.memory_view_window.activateWindow()

    def pushButton_Wiki_clicked(self):
        SysUtils.execute_shell_command_as_user('python3 -m webbrowser "https://github.com/korcankaraokcu/PINCE/wiki"')

    def pushButton_About_clicked(self):
        self.about_widget.show()
        self.about_widget.activateWindow()

    def pushButton_Settings_clicked(self):
        settings_dialog = SettingsDialogForm(self.set_default_settings)
        if settings_dialog.exec_():
            self.apply_settings()

    def pushButton_Console_clicked(self):
        console_widget = ConsoleWidgetForm()
        console_widget.showMaximized()

    def checkBox_Hex_stateChanged(self, state):
        if state == Qt.Checked:
            # allows only things that are hex, can also start with 0x
            self.lineEdit_Scan.setValidator(QRegExpValidator(QRegExp("(0x)?[A-Fa-f0-9]*$"), parent=self.lineEdit_Scan))
        else:
            # sets it back to integers only
            self.lineEdit_Scan.setValidator(QRegExpValidator(QRegExp("-?[0-9]*"), parent=self.lineEdit_Scan))

    # TODO add a damn keybind for this...
    def pushButton_NewFirstScan_clicked(self):
        if self.pushButton_NextScan.isEnabled():
            self.backend.send_command("reset")
            self.tableWidget_valuesearchtable.setRowCount(0)
            self.comboBox_ValueType.setEnabled(True)
            self.pushButton_NextScan.setEnabled(False)
        else:
            if not self.lineEdit_Scan.text():
                return
            self.comboBox_ValueType.setEnabled(False)
            self.pushButton_NextScan.setEnabled(True)
            self.pushButton_NextScan_clicked()  # makes code a little simpler to just implement everything in nextscan
        return

    # :doc:
    # adds things like 0x when searching for etc, basically just makes the line valid for scanmem
    # this should cover most things, more things might be added later if need be
    def validate_search(self, search_for):
        current_index = self.comboBox_ScanType.currentIndex()
        if current_index != 0:
            index_to_symbol = {
                1: "+",  # increased
                2: "-",  # decreased
                3: "<",  # less than
                4: ">",  # more than
                5: "!=",  # changed
                6: "="  # unchanged
            }
            return index_to_symbol[current_index]

        # none of theese should be possible to be true at the same time
        # TODO refactor later to use current index, and compare to type_defs constant
        if self.comboBox_ValueType.currentText() == "float":
            search_for.replace(".",
                               ",")  # this is odd, since when searching for floats from command line it uses `.` and not `,`
        elif self.comboBox_ValueType.currentText() == "string":
            search_for = "\" " + search_for
        elif self.checkBox_Hex.isChecked():
            if not search_for.startswith("0x"):
                search_for = "0x" + search_for
        return search_for

    def pushButton_NextScan_clicked(self):
        line_edit_text = self.lineEdit_Scan.text()
        if not line_edit_text:
            return
        search_for = self.validate_search(line_edit_text)

        # TODO add some validation for the search command
        self.backend.send_command(search_for)
        matches = self.backend.matches()
        self.label_MatchCount.setText("Match count: {}".format(self.backend.get_match_count()))
        self.tableWidget_valuesearchtable.setRowCount(0)

        for n, address, offset, region_type, value, t in matches:
            n = int(n)
            self.tableWidget_valuesearchtable.insertRow(
                self.tableWidget_valuesearchtable.rowCount())
            self.tableWidget_valuesearchtable.setItem(n, 0, QTableWidgetItem("0x" + address))
            self.tableWidget_valuesearchtable.setItem(n, 1, QTableWidgetItem(value))
            self.tableWidget_valuesearchtable.setItem(n, 2, QTableWidgetItem(value))
        return

    @GDB_Engine.execute_with_temporary_interruption
    def tableWidget_valuesearchtable_cell_double_clicked(self, row, col):
        addr = self.tableWidget_valuesearchtable.item(row, 0).text()
        self.add_entry_to_addresstable("", addr, self.comboBox_ValueType.currentIndex())

    def comboBox_ValueType_textChanged(self, text):
        # used for making our types in the combo box into what scanmem uses
        PINCE_TYPES_TO_SCANMEM = {
            "Byte": "int8",
            "2 Bytes": "int16",
            "4 Bytes": "int32",
            "8 Bytes": "int64",
            "Float": "float32",
            "Double": "float64",
            "String": "string",
            "Array of bytes": "bytearray"
        }

        validator_map = {
            "int": QRegExpValidator(QRegExp("-?[0-9]*"), parent=self.lineEdit_Scan),  # integers
            "float": QRegExpValidator(QRegExp("-?[0-9]+[.,]?[0-9]*")),
            # floats, should work fine with the small amount of testing I did
            "bytearray": QRegExpValidator(QRegExp("^(([A-Fa-f0-9]{2} +)+)$"), parent=self.lineEdit_Scan),
            # array of bytes
            "string": None
        }

        scanmem_type = PINCE_TYPES_TO_SCANMEM[text]
        validator_str = scanmem_type  # used to get the correct validator

        # TODO this can probably be made to look nicer, though it doesn't really matter
        if "int" in validator_str:
            validator_str = "int"
            self.checkBox_Hex.setEnabled(True)
        else:
            self.checkBox_Hex.setChecked(False)
            self.checkBox_Hex.setEnabled(False)
        if "float" in validator_str:
            validator_str = "float"

        self.lineEdit_Scan.setValidator(validator_map[validator_str])
        self.backend.send_command("option scan_data_type {}".format(scanmem_type))
        # according to scanmem instructions you should always do `reset` after changing type
        self.backend.send_command("reset")

        # shows the process select window

    def pushButton_AttachProcess_clicked(self):
        self.processwindow = ProcessForm(self)
        self.processwindow.show()

    def pushButton_Open_clicked(self):
        pct_file_path = SysUtils.get_user_path(type_defs.USER_PATHS.CHEAT_TABLES_PATH)
        file_paths = QFileDialog.getOpenFileNames(self, "Open PCT file(s)", pct_file_path,
                                                  "PINCE Cheat Table (*.pct);;All files (*)")[0]
        if not file_paths:
            return
        if self.treeWidget_AddressTable.topLevelItemCount() > 0:
            if InputDialogForm(item_list=[("Clear existing address table?",)]).exec_():
                self.treeWidget_AddressTable.clear()

        for file_path in file_paths:
            content = SysUtils.load_file(file_path)
            if content is None:
                QMessageBox.information(self, "Error", "File " + file_path + " does not exist, " +
                                        "is inaccessible or contains invalid content. Terminating...")
                break
            self.insert_records(content, self.treeWidget_AddressTable.invisibleRootItem(),
                                self.treeWidget_AddressTable.topLevelItemCount())

    def pushButton_Save_clicked(self):
        pct_file_path = SysUtils.get_user_path(type_defs.USER_PATHS.CHEAT_TABLES_PATH)
        file_path = QFileDialog.getSaveFileName(self, "Save PCT file", pct_file_path,
                                                "PINCE Cheat Table (*.pct);;All files (*)")[0]
        if not file_path:
            return
        content = [self.read_address_table_recursively(self.treeWidget_AddressTable.topLevelItem(i))
                   for i in range(self.treeWidget_AddressTable.topLevelItemCount())]
        file_path = SysUtils.append_file_extension(file_path, "pct")
        if not SysUtils.save_file(content, file_path):
            QMessageBox.information(self, "Error", "Cannot save to file")

    # Returns: a bool value indicates whether the operation succeeded.
    def attach_to_pid(self, pid):
        attach_result = GDB_Engine.attach(pid, gdb_path=gdb_path)
        if attach_result[0] == type_defs.ATTACH_RESULT.ATTACH_SUCCESSFUL:
            GDB_Engine.set_logging(gdb_logging)
            self.backend.send_command("pid {}".format(pid))
            self.on_new_process()
            return True
        else:
            QMessageBox.information(app.focusWidget(), "Error", attach_result[1])
            return False

    # Returns: a bool value indicates whether the operation succeeded.
    def create_new_process(self, file_path, args, ld_preload_path):
        if GDB_Engine.create_process(file_path, args, ld_preload_path):
            GDB_Engine.set_logging(gdb_logging)
            self.on_new_process()
            return True
        else:
            QMessageBox.information(app.focusWidget(), "Error", "An error occurred while trying to create process")
            self.on_inferior_exit()
            return False

    # This is called whenever a new process is created/attached to by PINCE
    # in order to change the form appearance
    def on_new_process(self):
        # TODO add scanmem attachment here
        p = SysUtils.get_process_information(GDB_Engine.currentpid)
        self.label_SelectedProcess.setText(str(p.pid) + " - " + p.name())

        # enable scan GUI

    def delete_address_table_contents(self):
        confirm_dialog = InputDialogForm(item_list=[("This will clear the contents of address table\nProceed?",)])
        if confirm_dialog.exec_():
            self.treeWidget_AddressTable.clear()

    def on_inferior_exit(self):
        if GDB_Engine.currentpid == -1:
            self.on_status_running()
            GDB_Engine.init_gdb(gdb_path=gdb_path)
            GDB_Engine.set_logging(gdb_logging)
            self.label_SelectedProcess.setText("No Process Selected")

    def on_status_detached(self):
        self.label_SelectedProcess.setStyleSheet("color: blue")
        self.label_InferiorStatus.setText("[detached]")
        self.label_InferiorStatus.setVisible(True)
        self.label_InferiorStatus.setStyleSheet("color: blue")

    def on_status_stopped(self):
        self.label_SelectedProcess.setStyleSheet("color: red")
        self.label_InferiorStatus.setText("[stopped]")
        self.label_InferiorStatus.setVisible(True)
        self.label_InferiorStatus.setStyleSheet("color: red")
        self.update_address_table_manually()

    def on_status_running(self):
        self.label_SelectedProcess.setStyleSheet("")
        self.label_InferiorStatus.setVisible(False)

    # closes all windows on exit
    def closeEvent(self, event):
        GDB_Engine.detach()
        app.closeAllWindows()

    def add_entry_to_addresstable(self, description, address_expr, address_type, length=0, zero_terminate=True):
        current_row = QTreeWidgetItem()
        current_row.setCheckState(FROZEN_COL, Qt.Unchecked)
        address_type_text = GuiUtils.valuetype_to_text(address_type, length, zero_terminate)

        self.treeWidget_AddressTable.addTopLevelItem(current_row)
        self.change_address_table_entries(current_row, description, address_expr, address_type_text)
        self.show()  # In case of getting called from elsewhere
        self.activateWindow()

    def treeWidget_AddressTable_item_double_clicked(self, row, column):
        action_for_column = {
            VALUE_COL: self.treeWidget_AddressTable_edit_value,
            DESC_COL: self.treeWidget_AddressTable_edit_desc,
            ADDR_COL: self.treeWidget_AddressTable_edit_address,
            TYPE_COL: self.treeWidget_AddressTable_edit_type
        }
        action_for_column = collections.defaultdict(lambda *args: lambda: None, action_for_column)
        action_for_column[column]()

    def treeWidget_AddressTable_edit_value(self):
        row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        if not row:
            return
        value = row.text(VALUE_COL)
        value_index = GuiUtils.text_to_valuetype(
            row.text(TYPE_COL))[0]
        label_text = "Enter the new value"
        if type_defs.VALUE_INDEX.is_string(value_index):
            label_text += "\nPINCE doesn't automatically insert a null terminated string at the end" \
                          "\nCopy-paste this character(\0) if you need to insert it at somewhere"
        dialog = InputDialogForm(item_list=[(label_text, value)], parsed_index=0, value_index=value_index)
        if dialog.exec_():
            table_contents = []
            value_text = dialog.get_values()
            for row in self.treeWidget_AddressTable.selectedItems():
                address = row.text(ADDR_COL)
                value_type = row.text(TYPE_COL)
                value_index = GuiUtils.text_to_valuetype(value_type)[0]
                if type_defs.VALUE_INDEX.is_string(value_index) or value_index == type_defs.VALUE_INDEX.INDEX_AOB:
                    unknown_type = SysUtils.parse_string(value_text, value_index)
                    if unknown_type is not None:
                        length = len(unknown_type)
                        row.setText(TYPE_COL, GuiUtils.change_text_length(value_type, length))
                table_contents.append((address, value_index))
            GDB_Engine.write_memory_multiple(table_contents, value_text)
            self.update_address_table_manually()

    def treeWidget_AddressTable_edit_desc(self):
        row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        if not row:
            return
        description = row.text(DESC_COL)
        dialog = InputDialogForm(item_list=[("Enter the new description", description)])
        if dialog.exec_():
            description_text = dialog.get_values()
            for row in self.treeWidget_AddressTable.selectedItems():
                row.setText(DESC_COL, description_text)

    def treeWidget_AddressTable_edit_address(self):
        row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        if not row:
            return
        description, address_expr, value_type = self.read_address_table_entries(row=row)
        index, length, zero_terminate, byte_len = GuiUtils.text_to_valuetype(value_type)
        manual_address_dialog = ManualAddressDialogForm(description=description, address=address_expr, index=index,
                                                        length=length, zero_terminate=zero_terminate)
        manual_address_dialog.setWindowTitle("Edit Address")
        if manual_address_dialog.exec_():
            description, address_expr, address_type, length, zero_terminate = manual_address_dialog.get_values()
            address_type_text = GuiUtils.valuetype_to_text(value_index=address_type, length=length,
                                                           zero_terminate=zero_terminate)
            self.change_address_table_entries(row, description, address_expr, address_type_text)

    def treeWidget_AddressTable_edit_type(self):
        row = GuiUtils.get_current_item(self.treeWidget_AddressTable)
        if not row:
            return
        value_type = row.text(TYPE_COL)
        value_index, length, zero_terminate = GuiUtils.text_to_valuetype(value_type)[0:3]
        dialog = EditTypeDialogForm(index=value_index, length=length, zero_terminate=zero_terminate)
        if dialog.exec_():
            params = dialog.get_values()
            type_text = GuiUtils.valuetype_to_text(*params)
            for row in self.treeWidget_AddressTable.selectedItems():
                row.setText(TYPE_COL, type_text)
            self.update_address_table_manually()

    # Changes the column values of the given row
    def change_address_table_entries(self, row, description="", address_expr="", address_type=""):
        address = GDB_Engine.examine_expression(address_expr).address
        value = ''
        index, length, zero_terminate, byte_len = GuiUtils.text_to_valuetype(address_type)
        if address:
            value = GDB_Engine.read_memory(address, index, length, zero_terminate)

        assert isinstance(row, QTreeWidgetItem)
        row.setText(DESC_COL, description)
        row.setData(ADDR_COL, ADDR_EXPR_ROLE, address_expr)
        row.setText(ADDR_COL, address or address_expr)
        row.setText(TYPE_COL, address_type)
        row.setText(VALUE_COL, "" if value is None else str(value))

    # Returns the column values of the given row
    def read_address_table_entries(self, row):
        description = row.text(DESC_COL)
        address_expr = row.data(ADDR_COL, ADDR_EXPR_ROLE)
        value_type = row.text(TYPE_COL)
        return description, address_expr, value_type

    # Returns the values inside the given row and all of its descendants.
    # All values except the last are the same as read_address_table_entries output.
    # Last value is an iterable of information about its direct children.
    def read_address_table_recursively(self, row):
        return self.read_address_table_entries(row) + \
               ([self.read_address_table_recursively(row.child(i)) for i in range(row.childCount())],)


class SettingsDialogForm(QDialog, SettingsDialog):
    def __init__(self, set_default_settings_func, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.set_default_settings = set_default_settings_func
        self.hotkey_to_value = {}  # Dict[str:str]-->Dict[Hotkey.name:settings_value]

        # Yet another retarded hack, thanks to pyuic5 not supporting QKeySequenceEdit
        self.keySequenceEdit = QKeySequenceEdit()
        self.verticalLayout_Hotkey.addWidget(self.keySequenceEdit)
        self.listWidget_Options.currentRowChanged.connect(self.change_display)
        icons_directory = GuiUtils.get_icons_directory()
        self.pushButton_GDBPath.setIcon(QIcon(QPixmap(icons_directory + "/folder.png")))
        self.listWidget_Functions.currentRowChanged.connect(self.listWidget_Functions_current_row_changed)
        self.keySequenceEdit.keySequenceChanged.connect(self.keySequenceEdit_key_sequence_changed)
        self.pushButton_ClearHotkey.clicked.connect(self.pushButton_ClearHotkey_clicked)
        self.pushButton_ResetSettings.clicked.connect(self.pushButton_ResetSettings_clicked)
        self.pushButton_GDBPath.clicked.connect(self.pushButton_GDBPath_clicked)
        self.checkBox_AutoUpdateAddressTable.stateChanged.connect(self.checkBox_AutoUpdateAddressTable_state_changed)
        self.checkBox_AutoAttachRegex.stateChanged.connect(self.checkBox_AutoAttachRegex_state_changed)
        self.checkBox_AutoAttachRegex_state_changed()
        self.config_gui()

    def accept(self):
        try:
            current_table_update_interval = float(self.lineEdit_UpdateInterval.text())
        except:
            QMessageBox.information(self, "Error", "Update interval must be a float")
            return
        try:
            current_instructions_shown = int(self.lineEdit_InstructionsPerScroll.text())
        except:
            QMessageBox.information(self, "Error", "Instruction count must be an integer")
            return
        if current_instructions_shown < 1:
            QMessageBox.information(self, "Error", "Instruction count cannot be lower than 1" +
                                    "\nIt would be silly anyway, wouldn't it?")
            return
        if not self.checkBox_AutoUpdateAddressTable.isChecked():
            pass
        elif current_table_update_interval < 0:
            QMessageBox.information(self, "Error", "Update interval cannot be a negative number")
            return
        elif current_table_update_interval == 0:

            # Easter egg #2
            if not InputDialogForm(item_list=[("You are asking for it, aren't you?",)]).exec_():
                return
        elif current_table_update_interval < 0.1:
            if not InputDialogForm(item_list=[("Update interval should be bigger than 0.1 seconds" +
                                               "\nSetting update interval less than 0.1 seconds may cause slowdown"
                                               "\nProceed?",)]).exec_():
                return

        self.settings.setValue("General/auto_update_address_table", self.checkBox_AutoUpdateAddressTable.isChecked())
        if self.checkBox_AutoUpdateAddressTable.isChecked():
            self.settings.setValue("General/address_table_update_interval", current_table_update_interval)
        self.settings.setValue("General/show_messagebox_on_exception", self.checkBox_MessageBoxOnException.isChecked())
        self.settings.setValue("General/show_messagebox_on_toggle_attach",
                               self.checkBox_MessageBoxOnToggleAttach.isChecked())
        current_gdb_output_mode = type_defs.gdb_output_mode(self.checkBox_OutputModeAsync.isChecked(),
                                                            self.checkBox_OutputModeCommand.isChecked(),
                                                            self.checkBox_OutputModeCommandInfo.isChecked())
        self.settings.setValue("General/gdb_output_mode", current_gdb_output_mode)
        if self.checkBox_AutoAttachRegex.isChecked():
            try:
                re.compile(self.lineEdit_AutoAttachList.text())
            except:
                QMessageBox.information(self, "Error", self.lineEdit_AutoAttachList.text() + " isn't a valid regex")
                return
        self.settings.setValue("General/auto_attach_list", self.lineEdit_AutoAttachList.text())
        self.settings.setValue("General/logo_path", self.comboBox_Logo.currentText())
        self.settings.setValue("General/auto_attach_regex", self.checkBox_AutoAttachRegex.isChecked())
        for hotkey in Hotkeys.Hotkey.get_hotkeys():
            self.settings.setValue("Hotkeys/" + hotkey.name, self.hotkey_to_value[hotkey.name])
        if self.radioButton_SimpleDLopenCall.isChecked():
            injection_method = type_defs.INJECTION_METHOD.SIMPLE_DLOPEN_CALL
        elif self.radioButton_AdvancedInjection.isChecked():
            injection_method = type_defs.INJECTION_METHOD.ADVANCED_INJECTION
        self.settings.setValue("CodeInjection/code_injection_method", injection_method)
        self.settings.setValue("Disassemble/bring_disassemble_to_front",
                               self.checkBox_BringDisassembleToFront.isChecked())
        self.settings.setValue("Disassemble/instructions_per_scroll", current_instructions_shown)
        selected_gdb_path = self.lineEdit_GDBPath.text()
        current_gdb_path = self.settings.value("Debug/gdb_path", type=str)
        if selected_gdb_path != current_gdb_path:
            if InputDialogForm(item_list=[("You have changed the GDB path, reset GDB now?",)]).exec_():
                GDB_Engine.init_gdb(gdb_path=selected_gdb_path)
        self.settings.setValue("Debug/gdb_path", selected_gdb_path)
        self.settings.setValue("Debug/gdb_logging", self.checkBox_GDBLogging.isChecked())
        super(SettingsDialogForm, self).accept()

    def config_gui(self):
        self.settings = QSettings()
        self.checkBox_AutoUpdateAddressTable.setChecked(
            self.settings.value("General/auto_update_address_table", type=bool))
        self.lineEdit_UpdateInterval.setText(
            str(self.settings.value("General/address_table_update_interval", type=float)))
        self.checkBox_MessageBoxOnException.setChecked(
            self.settings.value("General/show_messagebox_on_exception", type=bool))
        self.checkBox_MessageBoxOnToggleAttach.setChecked(
            self.settings.value("General/show_messagebox_on_toggle_attach", type=bool))
        self.checkBox_OutputModeAsync.setChecked(self.settings.value("General/gdb_output_mode").async_output)
        self.checkBox_OutputModeCommand.setChecked(self.settings.value("General/gdb_output_mode").command_output)
        self.checkBox_OutputModeCommandInfo.setChecked(self.settings.value("General/gdb_output_mode").command_info)
        self.lineEdit_AutoAttachList.setText(self.settings.value("General/auto_attach_list", type=str))
        logo_directory = SysUtils.get_logo_directory()
        logo_list = SysUtils.search_files(logo_directory, "\.(png|jpg|jpeg|svg)$")
        self.comboBox_Logo.clear()
        for logo in logo_list:
            self.comboBox_Logo.addItem(QIcon(os.path.join(logo_directory, logo)), logo)
        self.comboBox_Logo.setCurrentIndex(logo_list.index(self.settings.value("General/logo_path", type=str)))
        self.checkBox_AutoAttachRegex.setChecked(self.settings.value("General/auto_attach_regex", type=bool))
        self.listWidget_Functions.clear()
        self.hotkey_to_value.clear()
        for hotkey in Hotkeys.Hotkey.get_hotkeys():
            self.listWidget_Functions.addItem(hotkey.desc)
            self.hotkey_to_value[hotkey.name] = self.settings.value("Hotkeys/" + hotkey.name)
        injection_method = self.settings.value("CodeInjection/code_injection_method", type=int)
        if injection_method == type_defs.INJECTION_METHOD.SIMPLE_DLOPEN_CALL:
            self.radioButton_SimpleDLopenCall.setChecked(True)
        elif injection_method == type_defs.INJECTION_METHOD.ADVANCED_INJECTION:
            self.radioButton_AdvancedInjection.setChecked(True)
        self.checkBox_BringDisassembleToFront.setChecked(
            self.settings.value("Disassemble/bring_disassemble_to_front", type=bool))
        self.lineEdit_InstructionsPerScroll.setText(
            str(self.settings.value("Disassemble/instructions_per_scroll", type=int)))
        self.lineEdit_GDBPath.setText(str(self.settings.value("Debug/gdb_path", type=str)))
        self.checkBox_GDBLogging.setChecked(self.settings.value("Debug/gdb_logging", type=bool))

    def change_display(self, index):
        self.stackedWidget.setCurrentIndex(index)

    def listWidget_Functions_current_row_changed(self, index):
        if index == -1:
            self.keySequenceEdit.clear()
        else:
            self.keySequenceEdit.setKeySequence(self.hotkey_to_value[Hotkeys.Hotkey.get_hotkeys()[index].name])

    def keySequenceEdit_key_sequence_changed(self):
        index = self.listWidget_Functions.currentIndex().row()
        if index == -1:
            self.keySequenceEdit.clear()
        else:
            self.hotkey_to_value[Hotkeys.Hotkey.get_hotkeys()[index].name] = self.keySequenceEdit.keySequence().toString()

    def pushButton_ClearHotkey_clicked(self):
        self.keySequenceEdit.clear()

    def pushButton_ResetSettings_clicked(self):
        confirm_dialog = InputDialogForm(item_list=[("This will reset to the default settings\nProceed?",)])
        if confirm_dialog.exec_():
            self.set_default_settings()
            self.config_gui()

    def checkBox_AutoUpdateAddressTable_state_changed(self):
        if self.checkBox_AutoUpdateAddressTable.isChecked():
            self.QWidget_UpdateInterval.setEnabled(True)
        else:
            self.QWidget_UpdateInterval.setEnabled(False)

    def checkBox_AutoAttachRegex_state_changed(self):
        if self.checkBox_AutoAttachRegex.isChecked():
            self.lineEdit_AutoAttachList.setPlaceholderText("Mouse over on this text for examples")
            self.lineEdit_AutoAttachList.setToolTip("'asdf|qwer' searches for asdf or qwer\n" +
                                                    "'[as]df' searches for both adf and sdf\n" +
                                                    "Use the char '\\' to escape special chars such as '['\n" +
                                                    "'\[asdf\]' searches for opcodes that contain '[asdf]'")
        else:
            self.lineEdit_AutoAttachList.setPlaceholderText("Separate processes with ;")
            self.lineEdit_AutoAttachList.setToolTip("")

    def pushButton_GDBPath_clicked(self):
        current_path = self.lineEdit_GDBPath.text()
        file_path = QFileDialog.getOpenFileName(self, "Select the gdb binary", os.path.dirname(current_path))[0]
        if file_path:
            self.lineEdit_GDBPath.setText(file_path)


class MemoryViewWindowForm(QMainWindow, MemoryViewWindow):
    process_stopped = pyqtSignal()
    process_running = pyqtSignal()

    def set_dynamic_debug_hotkeys(self):
        self.actionBreak.setText("Break[{}]".format(Hotkeys.break_hotkey.value))
        self.actionRun.setText("Run[{}]".format(Hotkeys.continue_hotkey.value))
        self.actionToggle_Attach.setText("Toggle Attach[{}]".format(Hotkeys.toggle_attach_hotkey.value))

    def set_debug_menu_shortcuts(self):
        self.shortcut_step = QShortcut(QKeySequence("F7"), self)
        self.shortcut_step.activated.connect(self.step_instruction)
        self.shortcut_step_over = QShortcut(QKeySequence("F8"), self)
        self.shortcut_step_over.activated.connect(self.step_over_instruction)
        self.shortcut_execute_till_return = QShortcut(QKeySequence("Shift+F8"), self)
        self.shortcut_execute_till_return.activated.connect(self.execute_till_return)
        self.shortcut_toggle_breakpoint = QShortcut(QKeySequence("F5"), self)
        self.shortcut_toggle_breakpoint.activated.connect(self.toggle_breakpoint)
        self.shortcut_set_address = QShortcut(QKeySequence("Shift+F4"), self)
        self.shortcut_set_address.activated.connect(self.set_address)

    def initialize_file_context_menu(self):
        self.actionLoad_Trace.triggered.connect(self.show_trace_window)

    def initialize_debug_context_menu(self):
        self.actionBreak.triggered.connect(GDB_Engine.interrupt_inferior)
        self.actionRun.triggered.connect(GDB_Engine.continue_inferior)
        self.actionToggle_Attach.triggered.connect(self.parent().toggle_attach_hotkey_pressed)
        self.actionStep.triggered.connect(self.step_instruction)
        self.actionStep_Over.triggered.connect(self.step_over_instruction)
        self.actionExecute_Till_Return.triggered.connect(self.execute_till_return)
        self.actionToggle_Breakpoint.triggered.connect(self.toggle_breakpoint)
        self.actionSet_Address.triggered.connect(self.set_address)

    def initialize_view_context_menu(self):
        self.actionBookmarks.triggered.connect(self.actionBookmarks_triggered)
        self.actionStackTrace_Info.triggered.connect(self.actionStackTrace_Info_triggered)
        self.actionBreakpoints.triggered.connect(self.actionBreakpoints_triggered)
        self.actionFunctions.triggered.connect(self.actionFunctions_triggered)
        self.actionGDB_Log_File.triggered.connect(self.actionGDB_Log_File_triggered)
        self.actionMemory_Regions.triggered.connect(self.actionMemory_Regions_triggered)
        self.actionReferenced_Strings.triggered.connect(self.actionReferenced_Strings_triggered)
        self.actionReferenced_Calls.triggered.connect(self.actionReferenced_Calls_triggered)

    def initialize_tools_context_menu(self):
        self.actionInject_so_file.triggered.connect(self.actionInject_so_file_triggered)
        self.actionCall_Function.triggered.connect(self.actionCall_Function_triggered)
        self.actionSearch_Opcode.triggered.connect(self.actionSearch_Opcode_triggered)
        self.actionDissect_Code.triggered.connect(self.actionDissect_Code_triggered)

    def initialize_help_context_menu(self):
        self.actionLibPINCE.triggered.connect(self.actionLibPINCE_triggered)

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent
        GuiUtils.center(self)
        self.updating_memoryview = False
        self.process_stopped.connect(self.on_process_stop)
        self.process_running.connect(self.on_process_running)
        self.set_debug_menu_shortcuts()
        self.set_dynamic_debug_hotkeys()
        self.initialize_file_context_menu()
        self.initialize_view_context_menu()
        self.initialize_debug_context_menu()
        self.initialize_tools_context_menu()
        self.initialize_help_context_menu()
        self.initialize_disassemble_view()
        self.initialize_register_view()
        self.initialize_stack_view()
        self.initialize_hex_view()

        self.label_HexView_Information.contextMenuEvent = self.label_HexView_Information_context_menu_event

        self.splitter_Disassemble_Registers.setStretchFactor(0, 1)
        self.splitter_MainMiddle.setStretchFactor(1, 1)
        self.widget_StackView.resize(420, self.widget_StackView.height())  # blaze it
        self.widget_Registers.resize(330, self.widget_Registers.height())

    def initialize_register_view(self):
        self.pushButton_ShowFloatRegisters.clicked.connect(self.pushButton_ShowFloatRegisters_clicked)

    def initialize_stack_view(self):
        self.stackedWidget_StackScreens.setCurrentWidget(self.StackTrace)
        self.tableWidget_StackTrace.setColumnWidth(STACKTRACE_RETURN_ADDRESS_COL, 350)

        self.tableWidget_Stack.contextMenuEvent = self.tableWidget_Stack_context_menu_event
        self.tableWidget_StackTrace.contextMenuEvent = self.tableWidget_StackTrace_context_menu_event
        self.tableWidget_Stack.itemDoubleClicked.connect(self.tableWidget_Stack_double_click)
        self.tableWidget_StackTrace.itemDoubleClicked.connect(self.tableWidget_StackTrace_double_click)

        # Saving the original function because super() doesn't work when we override functions like this
        self.tableWidget_Stack.keyPressEvent_original = self.tableWidget_Stack.keyPressEvent
        self.tableWidget_Stack.keyPressEvent = self.tableWidget_Stack_key_press_event

        # Saving the original function because super() doesn't work when we override functions like this
        self.tableWidget_StackTrace.keyPressEvent_original = self.tableWidget_StackTrace.keyPressEvent
        self.tableWidget_StackTrace.keyPressEvent = self.tableWidget_StackTrace_key_press_event

    def initialize_disassemble_view(self):
        self.tableWidget_Disassemble.setColumnWidth(DISAS_ADDR_COL, 300)
        self.tableWidget_Disassemble.setColumnWidth(DISAS_BYTES_COL, 150)
        self.tableWidget_Disassemble.setColumnWidth(DISAS_OPCODES_COL, 400)

        self.disassemble_last_selected_address_int = 0
        self.disassemble_currently_displayed_address = "0"
        self.widget_Disassemble.wheelEvent = self.widget_Disassemble_wheel_event

        self.tableWidget_Disassemble.wheelEvent = QEvent.ignore
        self.verticalScrollBar_Disassemble.wheelEvent = QEvent.ignore

        GuiUtils.center_scroll_bar(self.verticalScrollBar_Disassemble)
        self.verticalScrollBar_Disassemble.mouseReleaseEvent = self.verticalScrollBar_Disassemble_mouse_release_event

        self.disassemble_scroll_bar_timer = QTimer()
        self.disassemble_scroll_bar_timer.setInterval(100)
        self.disassemble_scroll_bar_timer.timeout.connect(self.check_disassemble_scrollbar)
        self.disassemble_scroll_bar_timer.start()

        # Format: [address1, address2, ...]
        self.tableWidget_Disassemble.travel_history = []

        # Format: {address1:comment1,address2:comment2, ...}
        self.tableWidget_Disassemble.bookmarks = {}

        # Saving the original function because super() doesn't work when we override functions like this
        self.tableWidget_Disassemble.keyPressEvent_original = self.tableWidget_Disassemble.keyPressEvent
        self.tableWidget_Disassemble.keyPressEvent = self.tableWidget_Disassemble_key_press_event
        self.tableWidget_Disassemble.contextMenuEvent = self.tableWidget_Disassemble_context_menu_event

        self.tableWidget_Disassemble.itemDoubleClicked.connect(self.tableWidget_Disassemble_item_double_clicked)
        self.tableWidget_Disassemble.itemSelectionChanged.connect(self.tableWidget_Disassemble_item_selection_changed)

    def initialize_hex_view(self):
        self.hex_view_last_selected_address_int = 0
        self.hex_view_current_region = type_defs.tuple_region_info(0, 0, None)
        self.widget_HexView.wheelEvent = self.widget_HexView_wheel_event
        self.tableView_HexView_Hex.contextMenuEvent = self.widget_HexView_context_menu_event
        self.tableView_HexView_Ascii.contextMenuEvent = self.widget_HexView_context_menu_event
        self.tableView_HexView_Hex.doubleClicked.connect(self.exec_hex_view_edit_dialog)
        self.tableView_HexView_Ascii.doubleClicked.connect(self.exec_hex_view_edit_dialog)

        # Saving the original function because super() doesn't work when we override functions like this
        self.tableView_HexView_Hex.keyPressEvent_original = self.tableView_HexView_Hex.keyPressEvent
        self.tableView_HexView_Hex.keyPressEvent = self.widget_HexView_key_press_event
        self.tableView_HexView_Ascii.keyPressEvent = self.widget_HexView_key_press_event

        self.verticalScrollBar_HexView.wheelEvent = QEvent.ignore
        self.tableWidget_HexView_Address.wheelEvent = QEvent.ignore
        self.scrollArea_Hex.keyPressEvent = QEvent.ignore
        self.tableWidget_HexView_Address.setAutoScroll(False)
        self.tableWidget_HexView_Address.setStyleSheet("QTableWidget {background-color: transparent;}")
        self.tableWidget_HexView_Address.setSelectionMode(QAbstractItemView.NoSelection)

        self.hex_model = QHexModel(HEX_VIEW_ROW_COUNT, HEX_VIEW_COL_COUNT)
        self.ascii_model = QAsciiModel(HEX_VIEW_ROW_COUNT, HEX_VIEW_COL_COUNT)
        self.tableView_HexView_Hex.setModel(self.hex_model)
        self.tableView_HexView_Ascii.setModel(self.ascii_model)

        self.tableView_HexView_Hex.selectionModel().currentChanged.connect(self.on_hex_view_current_changed)
        self.tableView_HexView_Ascii.selectionModel().currentChanged.connect(self.on_ascii_view_current_changed)

        self.scrollArea_Hex.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea_Hex.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget_HexView_Address.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget_HexView_Address.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget_HexView_Address.verticalHeader().setDefaultSectionSize(
            self.tableView_HexView_Hex.verticalHeader().defaultSectionSize())

        GuiUtils.center_scroll_bar(self.verticalScrollBar_HexView)
        self.hex_view_scroll_bar_timer = QTimer()
        self.hex_view_scroll_bar_timer.setInterval(100)
        self.hex_view_scroll_bar_timer.timeout.connect(self.check_hex_view_scrollbar)
        self.hex_view_scroll_bar_timer.start()
        self.verticalScrollBar_HexView.mouseReleaseEvent = self.verticalScrollBar_HexView_mouse_release_event

    def show_trace_window(self):
        trace_instructions_window = TraceInstructionsWindowForm(prompt_dialog=False)
        trace_instructions_window.showMaximized()

    def step_instruction(self):
        if self.updating_memoryview:
            return
        GDB_Engine.step_instruction()

    def step_over_instruction(self):
        if self.updating_memoryview:
            return
        GDB_Engine.step_over_instruction()

    def execute_till_return(self):
        if self.updating_memoryview:
            return
        GDB_Engine.execute_till_return()

    def set_address(self):
        selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
        current_address_text = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL).text()
        current_address = SysUtils.extract_address(current_address_text)
        GDB_Engine.set_convenience_variable("pc", current_address)
        self.refresh_disassemble_view()

    @GDB_Engine.execute_with_temporary_interruption
    def toggle_breakpoint(self):
        selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
        current_address_text = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL).text()
        current_address = SysUtils.extract_address(current_address_text)
        current_address_int = int(current_address, 16)
        if GDB_Engine.check_address_in_breakpoints(current_address_int):
            GDB_Engine.delete_breakpoint(current_address)
        else:
            if not GDB_Engine.add_breakpoint(current_address):
                QMessageBox.information(self, "Error", "Failed to set breakpoint at address " + current_address)
        self.refresh_disassemble_view()

    def toggle_watchpoint(self, address, watchpoint_type=type_defs.WATCHPOINT_TYPE.BOTH):
        if GDB_Engine.check_address_in_breakpoints(address):
            GDB_Engine.delete_breakpoint(hex(address))
        else:
            watchpoint_dialog = InputDialogForm(item_list=[("Enter the watchpoint length in size of bytes", "")])
            if watchpoint_dialog.exec_():
                user_input = watchpoint_dialog.get_values()
                user_input_int = SysUtils.parse_string(user_input, type_defs.VALUE_INDEX.INDEX_4BYTES)
                if user_input_int is None:
                    QMessageBox.information(self, "Error", user_input + " can't be parsed as an integer")
                    return
                if user_input_int < 1:
                    QMessageBox.information(self, "Error", "Breakpoint length can't be lower than 1")
                    return
                if len(GDB_Engine.add_watchpoint(hex(address), user_input_int, watchpoint_type)) < 1:
                    QMessageBox.information(self, "Error", "Failed to set watchpoint at address " + hex(address))
        self.refresh_hex_view()

    def label_HexView_Information_context_menu_event(self, event):
        def copy_to_clipboard():
            app.clipboard().setText(self.label_HexView_Information.text())

        menu = QMenu()
        copy_label = menu.addAction("Copy to Clipboard")
        font_size = self.label_HexView_Information.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            copy_label: copy_to_clipboard
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def widget_HexView_context_menu_event(self, event):
        selected_address = self.tableView_HexView_Hex.get_selected_address()
        menu = QMenu()
        edit = menu.addAction("Edit")
        menu.addSeparator()
        go_to = menu.addAction("Go to expression[Ctrl+G]")
        disassemble = menu.addAction("Disassemble this address[Ctrl+D]")
        menu.addSeparator()
        add_address = menu.addAction("Add this address to address list[Ctrl+A]")
        menu.addSeparator()
        refresh = menu.addAction("Refresh[R]")
        menu.addSeparator()
        watchpoint_menu = menu.addMenu("Set Watchpoint")
        watchpoint_write = watchpoint_menu.addAction("Write Only")
        watchpoint_read = watchpoint_menu.addAction("Read Only")
        watchpoint_both = watchpoint_menu.addAction("Both")
        add_condition = menu.addAction("Add/Change condition for breakpoint")
        delete_breakpoint = menu.addAction("Delete Breakpoint")
        if not GDB_Engine.check_address_in_breakpoints(selected_address):
            GuiUtils.delete_menu_entries(menu, [add_condition, delete_breakpoint])
        else:
            GuiUtils.delete_menu_entries(menu, [watchpoint_menu.menuAction()])
        font_size = self.widget_HexView.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            edit: self.exec_hex_view_edit_dialog,
            go_to: self.exec_hex_view_go_to_dialog,
            disassemble: lambda: self.disassemble_expression(hex(selected_address), append_to_travel_history=True),
            add_address: self.exec_hex_view_add_address_dialog,
            refresh: self.refresh_hex_view,
            watchpoint_write: lambda: self.toggle_watchpoint(selected_address, type_defs.WATCHPOINT_TYPE.WRITE_ONLY),
            watchpoint_read: lambda: self.toggle_watchpoint(selected_address, type_defs.WATCHPOINT_TYPE.READ_ONLY),
            watchpoint_both: lambda: self.toggle_watchpoint(selected_address, type_defs.WATCHPOINT_TYPE.BOTH),
            add_condition: lambda: self.add_breakpoint_condition(selected_address),
            delete_breakpoint: lambda: self.toggle_watchpoint(selected_address)
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def exec_hex_view_edit_dialog(self):
        selected_address = self.tableView_HexView_Hex.get_selected_address()
        HexEditDialogForm(hex(selected_address)).exec_()
        self.refresh_hex_view()

    def exec_hex_view_go_to_dialog(self):
        current_address = hex(self.tableView_HexView_Hex.get_selected_address())
        go_to_dialog = InputDialogForm(item_list=[("Enter the expression", current_address)])
        if go_to_dialog.exec_():
            expression = go_to_dialog.get_values()
            dest_address = GDB_Engine.examine_expression(expression).address
            if not dest_address:
                QMessageBox.information(self, "Error", expression + " is invalid")
                return
            self.hex_dump_address(int(dest_address, 16))

    def exec_hex_view_add_address_dialog(self):
        selected_address = self.tableView_HexView_Hex.get_selected_address()
        manual_address_dialog = ManualAddressDialogForm(address=hex(selected_address),
                                                        index=type_defs.VALUE_INDEX.INDEX_AOB)
        if manual_address_dialog.exec_():
            description, address_expr, address_type, length, zero_terminate = manual_address_dialog.get_values()
            self.parent().add_entry_to_addresstable(description, address_expr, address_type, length, zero_terminate)

    def verticalScrollBar_HexView_mouse_release_event(self, event):
        GuiUtils.center_scroll_bar(self.verticalScrollBar_HexView)

    def verticalScrollBar_Disassemble_mouse_release_event(self, event):
        GuiUtils.center_scroll_bar(self.verticalScrollBar_Disassemble)

    def check_hex_view_scrollbar(self):
        if GDB_Engine.inferior_status != type_defs.INFERIOR_STATUS.INFERIOR_STOPPED:
            return
        maximum = self.verticalScrollBar_HexView.maximum()
        minimum = self.verticalScrollBar_HexView.minimum()
        midst = (maximum + minimum) / 2
        current_value = self.verticalScrollBar_HexView.value()
        if midst - 10 < current_value < midst + 10:
            return
        current_address = self.hex_model.current_address
        if current_value < midst:
            next_address = current_address - 0x40
        else:
            next_address = current_address + 0x40
        self.hex_dump_address(next_address)

    def check_disassemble_scrollbar(self):
        if GDB_Engine.inferior_status != type_defs.INFERIOR_STATUS.INFERIOR_STOPPED:
            return
        maximum = self.verticalScrollBar_Disassemble.maximum()
        minimum = self.verticalScrollBar_Disassemble.minimum()
        midst = (maximum + minimum) / 2
        current_value = self.verticalScrollBar_Disassemble.value()
        if midst - 10 < current_value < midst + 10:
            return
        if current_value < midst:
            self.tableWidget_Disassemble_scroll("previous", instructions_per_scroll)
        else:
            self.tableWidget_Disassemble_scroll("next", instructions_per_scroll)

    def on_hex_view_current_changed(self, QModelIndex_current):
        self.tableWidget_HexView_Address.setSelectionMode(QAbstractItemView.SingleSelection)
        self.hex_view_last_selected_address_int = self.tableView_HexView_Hex.get_selected_address()
        self.tableView_HexView_Ascii.selectionModel().setCurrentIndex(QModelIndex_current,
                                                                      QItemSelectionModel.ClearAndSelect)
        self.tableWidget_HexView_Address.selectRow(QModelIndex_current.row())
        self.tableWidget_HexView_Address.setSelectionMode(QAbstractItemView.NoSelection)

    def on_ascii_view_current_changed(self, QModelIndex_current):
        self.tableWidget_HexView_Address.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableView_HexView_Hex.selectionModel().setCurrentIndex(QModelIndex_current,
                                                                    QItemSelectionModel.ClearAndSelect)
        self.tableWidget_HexView_Address.selectRow(QModelIndex_current.row())
        self.tableWidget_HexView_Address.setSelectionMode(QAbstractItemView.NoSelection)

    # TODO: Consider merging HexView_Address, HexView_Hex and HexView_Ascii into one UI class
    # TODO: Move this function to that class if that happens
    # TODO: Also consider moving shared fields of HexView and HexModel to that class(such as HexModel.current_address)
    def hex_dump_address(self, int_address, offset=HEX_VIEW_ROW_COUNT * HEX_VIEW_COL_COUNT):
        int_address = SysUtils.modulo_address(int_address, GDB_Engine.inferior_arch)
        if not (self.hex_view_current_region.start <= int_address < self.hex_view_current_region.end):
            information = SysUtils.get_region_info(GDB_Engine.currentpid, int_address)
            if information:
                self.hex_view_current_region = information
                self.label_HexView_Information.setText("Protection:" + information.region.perms + " | Base:" +
                                                       hex(information.start) + "-" + hex(information.end))
            else:
                self.hex_view_current_region = type_defs.tuple_region_info(0, 0, None)
                self.label_HexView_Information.setText("This region is invalid")
        self.tableWidget_HexView_Address.setRowCount(0)
        self.tableWidget_HexView_Address.setRowCount(HEX_VIEW_ROW_COUNT * HEX_VIEW_COL_COUNT)
        for row, current_offset in enumerate(range(HEX_VIEW_ROW_COUNT)):
            row_address = hex(SysUtils.modulo_address(int_address + current_offset * 16, GDB_Engine.inferior_arch))
            self.tableWidget_HexView_Address.setItem(row, 0, QTableWidgetItem(row_address))
        tableWidget_HexView_column_size = self.tableWidget_HexView_Address.sizeHintForColumn(0) + 5
        self.tableWidget_HexView_Address.setMaximumWidth(tableWidget_HexView_column_size)
        self.tableWidget_HexView_Address.setMinimumWidth(tableWidget_HexView_column_size)
        self.tableWidget_HexView_Address.setColumnWidth(0, tableWidget_HexView_column_size)
        data_array, breakpoint_info = GDB_Engine.hex_dump(int_address, offset), GDB_Engine.get_breakpoint_info()
        self.hex_model.refresh(int_address, offset, data_array, breakpoint_info)
        self.ascii_model.refresh(int_address, offset, data_array, breakpoint_info)
        for index in range(offset):
            current_address = SysUtils.modulo_address(self.hex_model.current_address + index, GDB_Engine.inferior_arch)
            if current_address == self.hex_view_last_selected_address_int:
                row_index = int(index / HEX_VIEW_COL_COUNT)
                model_index = QModelIndex(self.hex_model.index(row_index, index % HEX_VIEW_COL_COUNT))
                self.tableView_HexView_Hex.selectionModel().setCurrentIndex(model_index,
                                                                            QItemSelectionModel.ClearAndSelect)
                self.tableView_HexView_Ascii.selectionModel().setCurrentIndex(model_index,
                                                                              QItemSelectionModel.ClearAndSelect)
                self.tableWidget_HexView_Address.setSelectionMode(QAbstractItemView.SingleSelection)
                self.tableWidget_HexView_Address.selectRow(row_index)
                self.tableWidget_HexView_Address.setSelectionMode(QAbstractItemView.NoSelection)
                break
        else:
            self.tableView_HexView_Hex.clearSelection()
            self.tableView_HexView_Ascii.clearSelection()

    def refresh_hex_view(self):
        if self.tableWidget_HexView_Address.rowCount() == 0:
            entry_point = GDB_Engine.find_entry_point()
            if not entry_point:
                # **Shrugs**
                entry_point = "0x00400000"
            self.hex_dump_address(int(entry_point, 16))
            self.tableView_HexView_Hex.resize_to_contents()
            self.tableView_HexView_Ascii.resize_to_contents()
        else:
            self.hex_dump_address(self.hex_model.current_address)

    # offset can also be an address as hex str
    # returns True if the given expression is disassembled correctly, False if not
    def disassemble_expression(self, expression, offset="+200", append_to_travel_history:bool = False) -> None:
        disas_data = GDB_Engine.disassemble(expression, offset)
        if not disas_data:
            QMessageBox.information(app.focusWidget(), "Error", "Cannot access memory at expression " + expression)
            return False
        program_counter = GDB_Engine.examine_expression("$pc").address
        program_counter_int = int(program_counter, 16)
        row_colour = {}
        breakpoint_info = GDB_Engine.get_breakpoint_info()

        # TODO: Change this nonsense when the huge refactorization happens
        current_first_address = SysUtils.extract_address(disas_data[0][0])  # address of first list entry
        try:
            previous_first_address = SysUtils.extract_address(
                self.tableWidget_Disassemble.item(0, DISAS_ADDR_COL).text())
        except AttributeError:
            previous_first_address = current_first_address

        self.tableWidget_Disassemble.setRowCount(0)
        self.tableWidget_Disassemble.setRowCount(len(disas_data))
        jmp_dict, call_dict = GDB_Engine.get_dissect_code_data(False, True, True)
        for row, item in enumerate(disas_data):
            comment = ""
            current_address = int(SysUtils.extract_address(item[0]), 16)
            current_address_str = hex(current_address)
            jmp_ref_exists = False
            call_ref_exists = False
            try:
                jmp_referrers = jmp_dict[current_address_str]
                jmp_ref_exists = True
            except KeyError:
                pass
            try:
                call_referrers = call_dict[current_address_str]
                call_ref_exists = True
            except KeyError:
                pass
            if jmp_ref_exists or call_ref_exists:
                tooltip_text = "Referenced by:\n"
                ref_count = 0
                if jmp_ref_exists:
                    for referrer in jmp_referrers:
                        if ref_count > 30:
                            break
                        tooltip_text += "\n" + hex(referrer) + "(" + jmp_referrers[referrer] + ")"
                        ref_count += 1
                if call_ref_exists:
                    for referrer in call_referrers:
                        if ref_count > 30:
                            break
                        tooltip_text += "\n" + hex(referrer) + "(call)"
                        ref_count += 1
                if ref_count > 30:
                    tooltip_text += "\n..."
                tooltip_text += "\n\nPress 'Ctrl+E' to see a detailed list of referrers"
                try:
                    row_colour[row].append(REF_COLOUR)
                except KeyError:
                    row_colour[row] = [REF_COLOUR]
                real_ref_count = 0
                if jmp_ref_exists:
                    real_ref_count += len(jmp_referrers)
                if call_ref_exists:
                    real_ref_count += len(call_referrers)
                item[0] = "{" + str(real_ref_count) + "}" + item[0]
            if current_address == program_counter_int:
                item[0] = ">>>" + item[0]
                try:
                    row_colour[row].append(PC_COLOUR)
                except KeyError:
                    row_colour[row] = [PC_COLOUR]
            for bookmark_item in self.tableWidget_Disassemble.bookmarks.keys():
                if current_address == bookmark_item:
                    try:
                        row_colour[row].append(BOOKMARK_COLOUR)
                    except KeyError:
                        row_colour[row] = [BOOKMARK_COLOUR]
                    item[0] = "(M)" + item[0]
                    comment = self.tableWidget_Disassemble.bookmarks[bookmark_item]
                    break
            for breakpoint in breakpoint_info:
                int_breakpoint_address = int(breakpoint.address, 16)
                if current_address == int_breakpoint_address:
                    try:
                        row_colour[row].append(BREAKPOINT_COLOUR)
                    except KeyError:
                        row_colour[row] = [BREAKPOINT_COLOUR]
                    breakpoint_mark = "(B"
                    if breakpoint.enabled == "n":
                        breakpoint_mark += "-disabled"
                    else:
                        if breakpoint.disp != "keep":
                            breakpoint_mark += "-" + breakpoint.disp
                        if breakpoint.enable_count:
                            breakpoint_mark += "-" + breakpoint.enable_count
                    breakpoint_mark += ")"
                    item[0] = breakpoint_mark + item[0]
                    break
            if current_address == self.disassemble_last_selected_address_int:
                self.tableWidget_Disassemble.selectRow(row)
            addr_item = QTableWidgetItem(item[0])
            bytes_item = QTableWidgetItem(item[1])
            opcodes_item = QTableWidgetItem(item[2])
            comment_item = QTableWidgetItem(comment)
            if jmp_ref_exists or call_ref_exists:
                addr_item.setToolTip(tooltip_text)
                bytes_item.setToolTip(tooltip_text)
                opcodes_item.setToolTip(tooltip_text)
                comment_item.setToolTip(tooltip_text)
            self.tableWidget_Disassemble.setItem(row, DISAS_ADDR_COL, addr_item)
            self.tableWidget_Disassemble.setItem(row, DISAS_BYTES_COL, bytes_item)
            self.tableWidget_Disassemble.setItem(row, DISAS_OPCODES_COL, opcodes_item)
            self.tableWidget_Disassemble.setItem(row, DISAS_COMMENT_COL, comment_item)
        jmp_dict.close()
        call_dict.close()
        self.handle_colours(row_colour)
        self.tableWidget_Disassemble.horizontalHeader().setStretchLastSection(True)

        # We append the old record to travel history as last action because we wouldn't like to see unnecessary
        # addresses in travel history if any error occurs while displaying the next location
        if append_to_travel_history:
            self.tableWidget_Disassemble.travel_history.append(previous_first_address)
        self.disassemble_currently_displayed_address = current_first_address
        return True

    def refresh_disassemble_view(self) -> None:
        self.disassemble_expression(self.disassemble_currently_displayed_address)

    # Set colour of a row if a specific address is encountered(e.g $pc, a bookmarked address etc.)
    def handle_colours(self, row_colour) -> None:
        for row in row_colour:
            current_row = row_colour[row]
            if PC_COLOUR in current_row:
                if BREAKPOINT_COLOUR in current_row:
                    colour = Qt.green
                elif BOOKMARK_COLOUR in current_row:
                    colour = Qt.yellow
                else:
                    colour = PC_COLOUR
                self.set_row_colour(row, colour)
                continue
            if BREAKPOINT_COLOUR in current_row:
                if BOOKMARK_COLOUR in current_row:
                    colour = Qt.magenta
                else:
                    colour = BREAKPOINT_COLOUR
                self.set_row_colour(row, colour)
                continue
            if BOOKMARK_COLOUR in current_row:
                self.set_row_colour(row, BOOKMARK_COLOUR)
                continue
            if REF_COLOUR in current_row:
                self.set_row_colour(row, REF_COLOUR)

    # color parameter should be Qt.colour
    def set_row_colour(self, row, colour) -> None:
        for col in range(self.tableWidget_Disassemble.columnCount()):
            self.tableWidget_Disassemble.item(row, col).setData(Qt.BackgroundColorRole, QColor(colour))

    def on_process_stop(self) -> None:
        if GDB_Engine.stop_reason == type_defs.STOP_REASON.PAUSE:
            self.setWindowTitle("Memory Viewer - Paused")
            return
        self.updating_memoryview = True
        time0 = time()
        thread_info = GDB_Engine.get_current_thread_information()
        if thread_info:
            self.setWindowTitle("Memory Viewer - Currently debugging " + thread_info)
        else:
            self.setWindowTitle("Error while getting thread information: " +
                                "Please invoke 'info threads' command in GDB Console and open an issue with the output")
        self.disassemble_expression("$pc")
        self.update_registers()
        if self.stackedWidget_StackScreens.currentWidget() == self.StackTrace:
            self.update_stacktrace()
        elif self.stackedWidget_StackScreens.currentWidget() == self.Stack:
            self.update_stack()
        self.refresh_hex_view()

        if bring_disassemble_to_front:
            self.activateWindow()
        try:
            if self.stacktrace_info_widget.isVisible():
                self.stacktrace_info_widget.update_stacktrace()
        except AttributeError:
            pass
        try:
            if self.float_registers_widget.isVisible():
                self.float_registers_widget.update_registers()
        except AttributeError:
            pass
        app.processEvents()
        time1 = time()
        print("UPDATED MEMORYVIEW IN:" + str(time1 - time0))
        self.updating_memoryview = False

    def on_process_running(self) -> None:
        self.setWindowTitle("Memory Viewer - Running")

    def add_breakpoint_condition(self, int_address: int):
        condition_text = "Enter the expression for condition, for instance:\n\n" + \
                         "$eax==0x523\n" + \
                         "$rax>0 && ($rbp<0 || $rsp==0)\n" + \
                         "printf($r10)==3"
        breakpoint = GDB_Engine.check_address_in_breakpoints(int_address)
        if breakpoint:
            condition_line_edit_text = breakpoint.condition
        else:
            condition_line_edit_text = ""
        condition_dialog = InputDialogForm(item_list=[(condition_text, condition_line_edit_text, Qt.AlignLeft)])
        if condition_dialog.exec_():
            condition = condition_dialog.get_values()
            if not GDB_Engine.modify_breakpoint(hex(int_address), type_defs.BREAKPOINT_MODIFY.CONDITION,
                                                condition=condition):
                QMessageBox.information(app.focusWidget(), "Error", "Failed to set condition for address " +
                                        hex(int_address) + "\nCheck terminal for details")

    def update_registers(self) -> None:
        registers = GDB_Engine.read_registers()
        if GDB_Engine.inferior_arch == type_defs.INFERIOR_ARCH.ARCH_64:
            self.stackedWidget.setCurrentWidget(self.registers_64)
            self.RAX.set_value(registers["rax"])
            self.RBX.set_value(registers["rbx"])
            self.RCX.set_value(registers["rcx"])
            self.RDX.set_value(registers["rdx"])
            self.RSI.set_value(registers["rsi"])
            self.RDI.set_value(registers["rdi"])
            self.RBP.set_value(registers["rbp"])
            self.RSP.set_value(registers["rsp"])
            self.RIP.set_value(registers["rip"])
            self.R8.set_value(registers["r8"])
            self.R9.set_value(registers["r9"])
            self.R10.set_value(registers["r10"])
            self.R11.set_value(registers["r11"])
            self.R12.set_value(registers["r12"])
            self.R13.set_value(registers["r13"])
            self.R14.set_value(registers["r14"])
            self.R15.set_value(registers["r15"])
        elif GDB_Engine.inferior_arch == type_defs.INFERIOR_ARCH.ARCH_32:
            self.stackedWidget.setCurrentWidget(self.registers_32)
            self.EAX.set_value(registers["eax"])
            self.EBX.set_value(registers["ebx"])
            self.ECX.set_value(registers["ecx"])
            self.EDX.set_value(registers["edx"])
            self.ESI.set_value(registers["esi"])
            self.EDI.set_value(registers["edi"])
            self.EBP.set_value(registers["ebp"])
            self.ESP.set_value(registers["esp"])
            self.EIP.set_value(registers["eip"])
        self.CF.set_value(registers["cf"])
        self.PF.set_value(registers["pf"])
        self.AF.set_value(registers["af"])
        self.ZF.set_value(registers["zf"])
        self.SF.set_value(registers["sf"])
        self.TF.set_value(registers["tf"])
        self.IF.set_value(registers["if"])
        self.DF.set_value(registers["df"])
        self.OF.set_value(registers["of"])
        self.CS.set_value(registers["cs"])
        self.SS.set_value(registers["ss"])
        self.DS.set_value(registers["ds"])
        self.ES.set_value(registers["es"])
        self.GS.set_value(registers["gs"])
        self.FS.set_value(registers["fs"])

    def update_stacktrace(self):
        stack_trace_info = GDB_Engine.get_stacktrace_info()
        self.tableWidget_StackTrace.setRowCount(0)
        self.tableWidget_StackTrace.setRowCount(len(stack_trace_info))
        for row, item in enumerate(stack_trace_info):
            self.tableWidget_StackTrace.setItem(row, STACKTRACE_RETURN_ADDRESS_COL, QTableWidgetItem(item[0]))
            self.tableWidget_StackTrace.setItem(row, STACKTRACE_FRAME_ADDRESS_COL, QTableWidgetItem(item[1]))

    def set_stack_widget(self, stack_widget):
        self.stackedWidget_StackScreens.setCurrentWidget(stack_widget)
        if stack_widget == self.Stack:
            self.update_stack()
        elif stack_widget == self.StackTrace:
            self.update_stacktrace()

    def tableWidget_StackTrace_context_menu_event(self, event):
        def copy_to_clipboard(row, column):
            app.clipboard().setText(self.tableWidget_StackTrace.item(row, column).text())

        selected_row = GuiUtils.get_current_row(self.tableWidget_StackTrace)

        menu = QMenu()
        switch_to_stack = menu.addAction("Full Stack")
        menu.addSeparator()
        clipboard_menu = menu.addMenu("Copy to Clipboard")
        copy_return = clipboard_menu.addAction("Copy Return Address")
        copy_frame = clipboard_menu.addAction("Copy Frame Address")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [clipboard_menu.menuAction()])
        refresh = menu.addAction("Refresh[R]")
        font_size = self.tableWidget_StackTrace.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            switch_to_stack: lambda: self.set_stack_widget(self.Stack),
            copy_return: lambda: copy_to_clipboard(selected_row, STACKTRACE_RETURN_ADDRESS_COL),
            copy_frame: lambda: copy_to_clipboard(selected_row, STACKTRACE_FRAME_ADDRESS_COL),
            refresh: self.update_stacktrace
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def update_stack(self):
        stack_info = GDB_Engine.get_stack_info()
        self.tableWidget_Stack.setRowCount(0)
        self.tableWidget_Stack.setRowCount(len(stack_info))
        for row, item in enumerate(stack_info):
            self.tableWidget_Stack.setItem(row, STACK_POINTER_ADDRESS_COL, QTableWidgetItem(item[0]))
            self.tableWidget_Stack.setItem(row, STACK_VALUE_COL, QTableWidgetItem(item[1]))
            self.tableWidget_Stack.setItem(row, STACK_POINTS_TO_COL, QTableWidgetItem(item[2]))
        self.tableWidget_Stack.resizeColumnToContents(STACK_POINTER_ADDRESS_COL)
        self.tableWidget_Stack.resizeColumnToContents(STACK_VALUE_COL)

    def tableWidget_Stack_key_press_event(self, event):
        selected_row = GuiUtils.get_current_row(self.tableWidget_Stack)
        current_address_text = self.tableWidget_Stack.item(selected_row, STACK_VALUE_COL).text()
        current_address = SysUtils.extract_address(current_address_text)

        actions = type_defs.KeyboardModifiersTupleDict([
            ((Qt.NoModifier, Qt.Key_R), self.update_stack),
            ((Qt.ControlModifier, Qt.Key_D),
             lambda: self.disassemble_expression(current_address, append_to_travel_history=True)),
            ((Qt.ControlModifier, Qt.Key_H), lambda: self.hex_dump_address(int(current_address, 16)))
        ])
        try:
            actions[event.modifiers(), event.key()]()
        except KeyError:
            pass
        self.tableWidget_Stack.keyPressEvent_original(event)

    def tableWidget_Stack_context_menu_event(self, event):
        def copy_to_clipboard(row, column):
            app.clipboard().setText(self.tableWidget_Stack.item(row, column).text())

        selected_row = GuiUtils.get_current_row(self.tableWidget_Stack)
        current_address_text = self.tableWidget_Stack.item(selected_row, STACK_VALUE_COL).text()
        current_address = SysUtils.extract_address(current_address_text)

        menu = QMenu()
        switch_to_stacktrace = menu.addAction("Stacktrace")
        menu.addSeparator()
        clipboard_menu = menu.addMenu("Copy to Clipboard")
        copy_address = clipboard_menu.addAction("Copy Address")
        copy_value = clipboard_menu.addAction("Copy Value")
        copy_points_to = clipboard_menu.addAction("Copy Points to")
        refresh = menu.addAction("Refresh[R]")
        menu.addSeparator()
        show_in_disas = menu.addAction("Disassemble 'value' pointer address[Ctrl+D]")
        show_in_hex = menu.addAction("Show 'value' pointer in HexView[Ctrl+H]")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [clipboard_menu.menuAction(), show_in_disas, show_in_hex])
        font_size = self.tableWidget_Stack.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            switch_to_stacktrace: lambda: self.set_stack_widget(self.StackTrace),
            copy_address: lambda: copy_to_clipboard(selected_row, STACK_POINTER_ADDRESS_COL),
            copy_value: lambda: copy_to_clipboard(selected_row, STACK_VALUE_COL),
            copy_points_to: lambda: copy_to_clipboard(selected_row, STACK_POINTS_TO_COL),
            refresh: self.update_stack,
            show_in_disas: lambda: self.disassemble_expression(current_address, append_to_travel_history=True),
            show_in_hex: lambda: self.hex_dump_address(int(current_address, 16))
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def tableWidget_Stack_double_click(self, index):
        selected_row = GuiUtils.get_current_row(self.tableWidget_Stack)
        if index.column() == STACK_POINTER_ADDRESS_COL:
            current_address_text = self.tableWidget_Stack.item(selected_row, STACK_POINTER_ADDRESS_COL).text()
            current_address = SysUtils.extract_address(current_address_text)
            self.hex_dump_address(int(current_address, 16))
        else:
            points_to_text = self.tableWidget_Stack.item(selected_row, STACK_POINTS_TO_COL).text()
            current_address_text = self.tableWidget_Stack.item(selected_row, STACK_VALUE_COL).text()
            current_address = SysUtils.extract_address(current_address_text)
            if points_to_text.startswith("(str)"):
                self.hex_dump_address(int(current_address, 16))
            else:
                self.disassemble_expression(current_address, append_to_travel_history=True)

    def tableWidget_StackTrace_double_click(self, index):
        selected_row = GuiUtils.get_current_row(self.tableWidget_StackTrace)
        if index.column() == STACKTRACE_RETURN_ADDRESS_COL:
            current_address_text = self.tableWidget_StackTrace.item(selected_row, STACKTRACE_RETURN_ADDRESS_COL).text()
            current_address = SysUtils.extract_address(current_address_text)
            self.disassemble_expression(current_address, append_to_travel_history=True)
        if index.column() == STACKTRACE_FRAME_ADDRESS_COL:
            current_address_text = self.tableWidget_StackTrace.item(selected_row, STACKTRACE_FRAME_ADDRESS_COL).text()
            current_address = SysUtils.extract_address(current_address_text)
            self.hex_dump_address(int(current_address, 16))

    def tableWidget_StackTrace_key_press_event(self, event):
        actions = type_defs.KeyboardModifiersTupleDict([
            ((Qt.NoModifier, Qt.Key_R), self.update_stacktrace)
        ])
        try:
            actions[event.modifiers(), event.key()]()
        except KeyError:
            pass
        self.tableWidget_StackTrace.keyPressEvent_original(event)

    def widget_Disassemble_wheel_event(self, event):
        steps = event.angleDelta()
        if steps.y() > 0:
            self.tableWidget_Disassemble_scroll("previous", instructions_per_scroll)
        else:
            self.tableWidget_Disassemble_scroll("next", instructions_per_scroll)

    def disassemble_check_viewport(self, where, instruction_count):
        current_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
        current_row_height = self.tableWidget_Disassemble.rowViewportPosition(current_row)
        row_height = self.tableWidget_Disassemble.verticalHeader().defaultSectionSize()
        max_height = self.tableWidget_Disassemble.maximumViewportSize().height()
        # visible_height = max_height - row_height
        height = max_height - row_height * 3  # lets us see the next 2 instructions after the last visible row
        if current_row_height > max_height:
            last_visible_row = 0
            for row in range(self.tableWidget_Disassemble.rowCount()):
                if self.tableWidget_Disassemble.rowViewportPosition(row) > height:
                    break
                last_visible_row += 1
            current_address = SysUtils.extract_address(
                self.tableWidget_Disassemble.item(current_row, DISAS_ADDR_COL).text())
            new_address = GDB_Engine.find_address_of_closest_instruction(current_address, "previous", last_visible_row)
            self.disassemble_expression(new_address)
        elif (where == "previous" and current_row == 0) or (where == "next" and current_row_height > height):
            self.tableWidget_Disassemble_scroll(where, instruction_count)

    def tableWidget_Disassemble_scroll(self, where, instruction_count):
        current_address = self.disassemble_currently_displayed_address
        new_address = GDB_Engine.find_address_of_closest_instruction(current_address, where, instruction_count)
        self.disassemble_expression(new_address)

    def widget_HexView_wheel_event(self, event):
        steps = event.angleDelta()
        current_address = self.hex_model.current_address
        if steps.y() > 0:
            next_address = current_address - 0x40
        else:
            next_address = current_address + 0x40
        self.hex_dump_address(next_address)

    def widget_HexView_key_press_event(self, event):
        selected_address = self.tableView_HexView_Hex.get_selected_address()

        actions = type_defs.KeyboardModifiersTupleDict([
            ((Qt.ControlModifier, Qt.Key_G), self.exec_hex_view_go_to_dialog),
            ((Qt.ControlModifier, Qt.Key_D),
             lambda: self.disassemble_expression(hex(selected_address), append_to_travel_history=True)),
            ((Qt.ControlModifier, Qt.Key_A), self.exec_hex_view_add_address_dialog),
            ((Qt.NoModifier, Qt.Key_R), self.refresh_hex_view)
        ])
        try:
            actions[event.modifiers(), event.key()]()
        except KeyError:
            pass
        self.tableView_HexView_Hex.keyPressEvent_original(event)

    def tableWidget_Disassemble_key_press_event(self, event):
        selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
        if selected_row is None:
            return
        current_address_text: str = ""
        current_address: str = ""
        current_address_int: int = 0

        try:
            disas_col = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL)
            logging.info("table widget item: {}".format(disas_col))
            if disas_col is None:
                logging.warning("could not fetch address")
            current_address_text = disas_col.text()
            current_address = SysUtils.extract_address(current_address_text)
            current_address_int = int(current_address, 16)
        except AttributeError as e:
            logging.exception("could not fetch address")

        actions = type_defs.KeyboardModifiersTupleDict([
            ((Qt.NoModifier, Qt.Key_Space), lambda: self.follow_instruction(selected_row)),
            ((Qt.ControlModifier, Qt.Key_E), lambda: self.exec_examine_referrers_widget(current_address_text)),
            ((Qt.ControlModifier, Qt.Key_G), self.exec_disassemble_go_to_dialog),
            ((Qt.ControlModifier, Qt.Key_H), lambda: self.hex_dump_address(current_address_int)),
            ((Qt.ControlModifier, Qt.Key_B), lambda: self.bookmark_address(current_address_int)),
            ((Qt.ControlModifier, Qt.Key_D), self.dissect_current_region),
            ((Qt.ControlModifier, Qt.Key_T), self.exec_trace_instructions_dialog),
            ((Qt.NoModifier, Qt.Key_R), self.refresh_disassemble_view),
            ((Qt.NoModifier, Qt.Key_Down), lambda: self.disassemble_check_viewport("next", 1)),
            ((Qt.NoModifier, Qt.Key_Up), lambda: self.disassemble_check_viewport("previous", 1))
        ])
        try:
            actions[event.modifiers(), event.key()]()
        except KeyError:
            pass
        self.tableWidget_Disassemble.keyPressEvent_original(event)

    def tableWidget_Disassemble_item_double_clicked(self, index):
        if index.column() == DISAS_COMMENT_COL:
            selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
            current_address_text = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL).text()
            current_address = int(SysUtils.extract_address(current_address_text), 16)
            if current_address in self.tableWidget_Disassemble.bookmarks:
                self.change_bookmark_comment(current_address)
            else:
                self.bookmark_address(current_address)

    def tableWidget_Disassemble_item_selection_changed(self):
        try:
            selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
            selected_address_text = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL).text()
            self.disassemble_last_selected_address_int = int(SysUtils.extract_address(selected_address_text), 16)
        except (TypeError, ValueError, AttributeError):
            pass

    # Search the item in given row for location changing instructions
    # Go to the address pointed by that instruction if it contains any
    def follow_instruction(self, selected_row):
        column = self.tableWidget_Disassemble.item(selected_row, DISAS_OPCODES_COL)
        if column is None:
            return
        address = SysUtils.instruction_follow_address(column.text())
        if address:
            self.disassemble_expression(address, append_to_travel_history=True)

    def disassemble_go_back(self):
        if self.tableWidget_Disassemble.travel_history:
            last_location = self.tableWidget_Disassemble.travel_history[-1]
            self.disassemble_expression(last_location)
            self.tableWidget_Disassemble.travel_history.pop()

    def tableWidget_Disassemble_context_menu_event(self, event):
        def copy_to_clipboard(row, column):
            app.clipboard().setText(self.tableWidget_Disassemble.item(row, column).text())

        def copy_all_columns(row):
            copied_string = ""
            for column in range(self.tableWidget_Disassemble.columnCount()):
                copied_string += self.tableWidget_Disassemble.item(row, column).text() + "\t"
            app.clipboard().setText(copied_string)

        selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
        current_address_text = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL).text()
        current_address = SysUtils.extract_address(current_address_text)
        current_address_int = int(current_address, 16)

        menu = QMenu()
        go_to = menu.addAction("Go to expression[Ctrl+G]")
        back = menu.addAction("Back")
        show_in_hex_view = menu.addAction("Show this address in HexView[Ctrl+H]")
        menu.addSeparator()
        followable = SysUtils.instruction_follow_address(
            self.tableWidget_Disassemble.item(selected_row, DISAS_OPCODES_COL).text())
        follow = menu.addAction("Follow[Space]")
        if not followable:
            GuiUtils.delete_menu_entries(menu, [follow])
        examine_referrers = menu.addAction("Examine Referrers[Ctrl+E]")
        if not GuiUtils.contains_reference_mark(current_address_text):
            GuiUtils.delete_menu_entries(menu, [examine_referrers])
        bookmark = menu.addAction("Bookmark this address[Ctrl+B]")
        delete_bookmark = menu.addAction("Delete this bookmark")
        change_comment = menu.addAction("Change comment")
        is_bookmarked = current_address_int in self.tableWidget_Disassemble.bookmarks
        if not is_bookmarked:
            GuiUtils.delete_menu_entries(menu, [delete_bookmark, change_comment])
        else:
            GuiUtils.delete_menu_entries(menu, [bookmark])
        go_to_bookmark = menu.addMenu("Go to bookmarked address")
        address_list = [hex(address) for address in self.tableWidget_Disassemble.bookmarks.keys()]
        bookmark_actions = [go_to_bookmark.addAction(item.all) for item in GDB_Engine.examine_expressions(address_list)]
        menu.addSeparator()
        toggle_breakpoint = menu.addAction("Toggle Breakpoint[F5]")
        add_condition = menu.addAction("Add/Change condition for breakpoint")
        if not GDB_Engine.check_address_in_breakpoints(current_address_int):
            GuiUtils.delete_menu_entries(menu, [add_condition])
        menu.addSeparator()
        track_breakpoint = menu.addAction("Find out which addresses this instruction accesses")
        trace_instructions = menu.addAction("Break and trace instructions[Ctrl+T]")
        dissect_region = menu.addAction("Dissect this region[Ctrl+D]")
        menu.addSeparator()
        refresh = menu.addAction("Refresh[R]")
        menu.addSeparator()
        clipboard_menu = menu.addMenu("Copy to Clipboard")
        copy_address = clipboard_menu.addAction("Copy Address")
        copy_bytes = clipboard_menu.addAction("Copy Bytes")
        copy_opcode = clipboard_menu.addAction("Copy Opcode")
        copy_comment = clipboard_menu.addAction("Copy Comment")
        copy_all = clipboard_menu.addAction("Copy All")
        font_size = self.tableWidget_Disassemble.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            go_to: self.exec_disassemble_go_to_dialog,
            back: self.disassemble_go_back,
            show_in_hex_view: lambda: self.hex_dump_address(current_address_int),
            follow: lambda: self.follow_instruction(selected_row),
            examine_referrers: lambda: self.exec_examine_referrers_widget(current_address_text),
            bookmark: lambda: self.bookmark_address(current_address_int),
            delete_bookmark: lambda: self.delete_bookmark(current_address_int),
            change_comment: lambda: self.change_bookmark_comment(current_address_int),
            toggle_breakpoint: self.toggle_breakpoint,
            add_condition: lambda: self.add_breakpoint_condition(current_address_int),
            track_breakpoint: self.exec_track_breakpoint_dialog,
            trace_instructions: self.exec_trace_instructions_dialog,
            dissect_region: self.dissect_current_region,
            refresh: self.refresh_disassemble_view,
            copy_address: lambda: copy_to_clipboard(selected_row, DISAS_ADDR_COL),
            copy_bytes: lambda: copy_to_clipboard(selected_row, DISAS_BYTES_COL),
            copy_opcode: lambda: copy_to_clipboard(selected_row, DISAS_OPCODES_COL),
            copy_comment: lambda: copy_to_clipboard(selected_row, DISAS_COMMENT_COL),
            copy_all: lambda: copy_all_columns(selected_row)
        }
        try:
            actions[action]()
        except KeyError:
            pass
        if action in bookmark_actions:
            self.disassemble_expression(SysUtils.extract_address(action.text()), append_to_travel_history=True)

    def dissect_current_region(self):
        selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
        current_address_text = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL).text()
        current_address = SysUtils.extract_address(current_address_text)
        dissect_code_dialog = DissectCodeDialogForm(int_address=int(current_address, 16))
        dissect_code_dialog.scan_finished_signal.connect(dissect_code_dialog.accept)
        dissect_code_dialog.exec_()
        self.refresh_disassemble_view()

    def exec_examine_referrers_widget(self, current_address_text):
        if not GuiUtils.contains_reference_mark(current_address_text):
            return
        current_address = SysUtils.extract_address(current_address_text)
        current_address_int = int(current_address, 16)
        examine_referrers_widget = ExamineReferrersWidgetForm(current_address_int, self)
        examine_referrers_widget.show()

    def exec_trace_instructions_dialog(self):
        selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
        current_address_text = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL).text()
        current_address = SysUtils.extract_address(current_address_text)
        trace_instructions_window = TraceInstructionsWindowForm(current_address, parent=self)
        trace_instructions_window.showMaximized()

    def exec_track_breakpoint_dialog(self):
        selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
        current_address_text = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL).text()
        current_address = SysUtils.extract_address(current_address_text)
        current_instruction = self.tableWidget_Disassemble.item(selected_row, DISAS_OPCODES_COL).text()
        track_breakpoint_widget = TrackBreakpointWidgetForm(current_address, current_instruction, self)
        track_breakpoint_widget.show()

    def exec_disassemble_go_to_dialog(self):
        selected_row = GuiUtils.get_current_row(self.tableWidget_Disassemble)
        current_address_text = self.tableWidget_Disassemble.item(selected_row, DISAS_ADDR_COL).text()
        current_address = SysUtils.extract_address(current_address_text)

        go_to_dialog = InputDialogForm(item_list=[("Enter the expression", current_address)])
        if go_to_dialog.exec_():
            traveled_exp = go_to_dialog.get_values()
            self.disassemble_expression(traveled_exp, append_to_travel_history=True)

    def bookmark_address(self, int_address):
        if int_address in self.tableWidget_Disassemble.bookmarks:
            QMessageBox.information(app.focusWidget(), "Error", "This address has already been bookmarked")
            return
        comment_dialog = InputDialogForm(item_list=[("Enter the comment for bookmarked address", "")])
        if comment_dialog.exec_():
            comment = comment_dialog.get_values()
        else:
            return
        self.tableWidget_Disassemble.bookmarks[int_address] = comment
        self.refresh_disassemble_view()

    def change_bookmark_comment(self, int_address):
        current_comment = self.tableWidget_Disassemble.bookmarks[int_address]
        comment_dialog = InputDialogForm(item_list=[("Enter the comment for bookmarked address", current_comment)])
        if comment_dialog.exec_():
            new_comment = comment_dialog.get_values()
        else:
            return
        self.tableWidget_Disassemble.bookmarks[int_address] = new_comment
        self.refresh_disassemble_view()

    def delete_bookmark(self, int_address):
        if int_address in self.tableWidget_Disassemble.bookmarks:
            del self.tableWidget_Disassemble.bookmarks[int_address]
            self.refresh_disassemble_view()

    def actionBookmarks_triggered(self):
        bookmark_widget = BookmarkWidgetForm(self)
        bookmark_widget.show()
        bookmark_widget.activateWindow()

    def actionStackTrace_Info_triggered(self):
        self.stacktrace_info_widget = StackTraceInfoWidgetForm()
        self.stacktrace_info_widget.show()

    def actionBreakpoints_triggered(self):
        breakpoint_widget = BreakpointInfoWidgetForm(self)
        breakpoint_widget.show()
        breakpoint_widget.activateWindow()

    def actionFunctions_triggered(self):
        functions_info_widget = FunctionsInfoWidgetForm(self)
        functions_info_widget.show()

    def actionGDB_Log_File_triggered(self):
        log_file_widget = LogFileWidgetForm()
        log_file_widget.showMaximized()

    def actionMemory_Regions_triggered(self):
        memory_regions_widget = MemoryRegionsWidgetForm(self)
        memory_regions_widget.show()

    def actionReferenced_Strings_triggered(self):
        ref_str_widget = ReferencedStringsWidgetForm(self)
        ref_str_widget.show()

    def actionReferenced_Calls_triggered(self):
        ref_call_widget = ReferencedCallsWidgetForm(self)
        ref_call_widget.show()

    def actionInject_so_file_triggered(self):
        file_path = QFileDialog.getOpenFileName(self, "Select the .so file", "", "Shared object library (*.so)")[0]
        if file_path:
            if GDB_Engine.inject_with_dlopen_call(file_path):
                QMessageBox.information(self, "Success!", "The file has been injected")
            else:
                QMessageBox.information(self, "Error", "Failed to inject the .so file")

    def actionCall_Function_triggered(self):
        label_text = "Enter the expression for the function that'll be called from the inferior" \
                     "\nYou can view functions list from View->Functions" \
                     "\n\nFor instance:" \
                     '\nCalling printf("1234") will yield something like this' \
                     '\n↓' \
                     '\n$28 = 4' \
                     '\n\n$28 is the assigned convenience variable' \
                     '\n4 is the result' \
                     '\nYou can use the assigned variable from the GDB Console'
        call_dialog = InputDialogForm(item_list=[(label_text, "")])
        if call_dialog.exec_():
            result = GDB_Engine.call_function_from_inferior(call_dialog.get_values())
            if result[0]:
                QMessageBox.information(self, "Success!", result[0] + " = " + result[1])
            else:
                QMessageBox.information(self, "Failed", "Failed to call the expression " + call_dialog.get_values())

    def actionSearch_Opcode_triggered(self):
        start_address = int(self.disassemble_currently_displayed_address, 16)
        end_address = start_address + 0x30000
        search_opcode_widget = SearchOpcodeWidgetForm(hex(start_address), hex(end_address), self)
        search_opcode_widget.show()

    def actionDissect_Code_triggered(self):
        self.dissect_code_dialog = DissectCodeDialogForm()
        self.dissect_code_dialog.exec_()
        self.refresh_disassemble_view()

    def actionLibPINCE_triggered(self):
        libPINCE_widget = LibPINCEReferenceWidgetForm(is_window=True)
        libPINCE_widget.showMaximized()

    def pushButton_ShowFloatRegisters_clicked(self):
        self.float_registers_widget = FloatRegisterWidgetForm()
        self.float_registers_widget.show()
        GuiUtils.center_to_window(self.float_registers_widget, self.widget_Registers)


class FloatRegisterWidgetForm(QTabWidget, FloatRegisterWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        self.update_registers()
        self.tableWidget_FPU.itemDoubleClicked.connect(self.set_register)
        self.tableWidget_XMM.itemDoubleClicked.connect(self.set_register)

    def update_registers(self):
        self.tableWidget_FPU.setRowCount(0)
        self.tableWidget_FPU.setRowCount(8)
        self.tableWidget_XMM.setRowCount(0)
        self.tableWidget_XMM.setRowCount(8)
        float_registers = GDB_Engine.read_float_registers()
        for row, (st, xmm) in enumerate(zip(type_defs.REGISTERS.FLOAT.ST, type_defs.REGISTERS.FLOAT.XMM)):
            self.tableWidget_FPU.setItem(row, FLOAT_REGISTERS_NAME_COL, QTableWidgetItem(st))
            self.tableWidget_FPU.setItem(row, FLOAT_REGISTERS_VALUE_COL, QTableWidgetItem(float_registers[st]))
            self.tableWidget_XMM.setItem(row, FLOAT_REGISTERS_NAME_COL, QTableWidgetItem(xmm))
            self.tableWidget_XMM.setItem(row, FLOAT_REGISTERS_VALUE_COL, QTableWidgetItem(float_registers[xmm]))

    def set_register(self, index):
        current_row = index.row()
        if self.currentWidget() == self.FPU:
            current_table_widget = self.tableWidget_FPU
        elif self.currentWidget() == self.XMM:
            current_table_widget = self.tableWidget_XMM
        else:
            raise Exception("Current widget is invalid: " + str(self.currentWidget().objectName()))
        current_register = current_table_widget.item(current_row, FLOAT_REGISTERS_NAME_COL).text()
        current_value = current_table_widget.item(current_row, FLOAT_REGISTERS_VALUE_COL).text()
        label_text = "Enter the new value of register " + current_register.upper()
        register_dialog = InputDialogForm(item_list=[(label_text, current_value)])
        if register_dialog.exec_():
            if self.currentWidget() == self.XMM:
                current_register += ".v4_float"
            GDB_Engine.set_convenience_variable(current_register, register_dialog.get_values())
            self.update_registers()


class StackTraceInfoWidgetForm(QWidget, StackTraceInfoWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        GuiUtils.center(self)
        self.setWindowFlags(Qt.Window)
        self.listWidget_ReturnAddresses.currentRowChanged.connect(self.update_frame_info)
        self.update_stacktrace()

    def update_stacktrace(self):
        self.listWidget_ReturnAddresses.clear()
        return_addresses = GDB_Engine.get_stack_frame_return_addresses()
        self.listWidget_ReturnAddresses.addItems(return_addresses)

    def update_frame_info(self, index):
        frame_info = GDB_Engine.get_stack_frame_info(index)
        self.textBrowser_Info.setText(frame_info)


class BreakpointInfoWidgetForm(QTabWidget, BreakpointInfoWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center(self)
        self.setWindowFlags(Qt.Window)
        self.tableWidget_BreakpointInfo.contextMenuEvent = self.tableWidget_BreakpointInfo_context_menu_event

        # Saving the original function because super() doesn't work when we override functions like this
        self.tableWidget_BreakpointInfo.keyPressEvent_original = self.tableWidget_BreakpointInfo.keyPressEvent
        self.tableWidget_BreakpointInfo.keyPressEvent = self.tableWidget_BreakpointInfo_key_press_event
        self.tableWidget_BreakpointInfo.itemDoubleClicked.connect(self.tableWidget_BreakpointInfo_double_clicked)
        self.refresh()

    def refresh(self):
        break_info = GDB_Engine.get_breakpoint_info()
        self.tableWidget_BreakpointInfo.setRowCount(0)
        self.tableWidget_BreakpointInfo.setRowCount(len(break_info))
        for row, item in enumerate(break_info):
            self.tableWidget_BreakpointInfo.setItem(row, Break.NUM_COL, QTableWidgetItem(item.number))
            self.tableWidget_BreakpointInfo.setItem(row, Break.TYPE_COL, QTableWidgetItem(item.breakpoint_type))
            self.tableWidget_BreakpointInfo.setItem(row, Break.DISP_COL, QTableWidgetItem(item.disp))
            self.tableWidget_BreakpointInfo.setItem(row, Break.ENABLED_COL, QTableWidgetItem(item.enabled))
            self.tableWidget_BreakpointInfo.setItem(row, Break.ADDR_COL, QTableWidgetItem(item.address))
            self.tableWidget_BreakpointInfo.setItem(row, Break.SIZE_COL, QTableWidgetItem(str(item.size)))
            self.tableWidget_BreakpointInfo.setItem(row, Break.ON_HIT_COL, QTableWidgetItem(item.on_hit))
            self.tableWidget_BreakpointInfo.setItem(row, Break.HIT_COUNT_COL, QTableWidgetItem(item.hit_count))
            self.tableWidget_BreakpointInfo.setItem(row, Break.COND_COL, QTableWidgetItem(item.condition))
        self.tableWidget_BreakpointInfo.resizeColumnsToContents()
        self.tableWidget_BreakpointInfo.horizontalHeader().setStretchLastSection(True)
        self.textBrowser_BreakpointInfo.clear()
        self.textBrowser_BreakpointInfo.setText(GDB_Engine.send_command("info break", cli_output=True))

    def delete_breakpoint(self, address):
        if address is not None:
            GDB_Engine.delete_breakpoint(address)
            self.refresh_all()

    def tableWidget_BreakpointInfo_key_press_event(self, event):
        selected_row = GuiUtils.get_current_row(self.tableWidget_BreakpointInfo)
        if selected_row != -1:
            current_address_text = self.tableWidget_BreakpointInfo.item(selected_row, Break.ADDR_COL).text()
            current_address = SysUtils.extract_address(current_address_text)
        else:
            current_address = None

        actions = type_defs.KeyboardModifiersTupleDict([
            ((Qt.NoModifier, Qt.Key_Delete), lambda: self.delete_breakpoint(current_address)),
            ((Qt.NoModifier, Qt.Key_R), self.refresh)
        ])
        try:
            actions[event.modifiers(), event.key()]()
        except KeyError:
            pass
        self.tableWidget_BreakpointInfo.keyPressEvent_original(event)

    def exec_enable_count_dialog(self, current_address):
        hit_count_dialog = InputDialogForm(item_list=[("Enter the hit count(1 or higher)", "")])
        if hit_count_dialog.exec_():
            count = hit_count_dialog.get_values()
            try:
                count = int(count)
            except ValueError:
                QMessageBox.information(self, "Error", "Hit count must be an integer")
            else:
                if count < 1:
                    QMessageBox.information(self, "Error", "Hit count can't be lower than 1")
                else:
                    GDB_Engine.modify_breakpoint(current_address, type_defs.BREAKPOINT_MODIFY.ENABLE_COUNT,
                                                 count=count)

    def tableWidget_BreakpointInfo_context_menu_event(self, event):
        selected_row = GuiUtils.get_current_row(self.tableWidget_BreakpointInfo)
        if selected_row != -1:
            current_address_text = self.tableWidget_BreakpointInfo.item(selected_row, Break.ADDR_COL).text()
            current_address = SysUtils.extract_address(current_address_text)
            current_address_int = int(current_address, 16)
        else:
            current_address = None
            current_address_int = None

        menu = QMenu()
        change_condition = menu.addAction("Change condition of this breakpoint")
        enable = menu.addAction("Enable this breakpoint")
        disable = menu.addAction("Disable this breakpoint")
        enable_once = menu.addAction("Disable this breakpoint after hit")
        enable_count = menu.addAction("Disable this breakpoint after X hits")
        enable_delete = menu.addAction("Delete this breakpoint after hit")
        menu.addSeparator()
        delete_breakpoint = menu.addAction("Delete this breakpoint[Del]")
        menu.addSeparator()
        if current_address is None:
            deletion_list = [change_condition, enable, disable, enable_once, enable_count, enable_delete,
                             delete_breakpoint]
            GuiUtils.delete_menu_entries(menu, deletion_list)
        refresh = menu.addAction("Refresh[R]")
        font_size = self.tableWidget_BreakpointInfo.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            change_condition: lambda: self.parent().add_breakpoint_condition(current_address_int),
            enable: lambda: GDB_Engine.modify_breakpoint(current_address, type_defs.BREAKPOINT_MODIFY.ENABLE),
            disable: lambda: GDB_Engine.modify_breakpoint(current_address, type_defs.BREAKPOINT_MODIFY.DISABLE),
            enable_once: lambda: GDB_Engine.modify_breakpoint(current_address, type_defs.BREAKPOINT_MODIFY.ENABLE_ONCE),
            enable_count: lambda: self.exec_enable_count_dialog(current_address),
            enable_delete: lambda: GDB_Engine.modify_breakpoint(current_address,
                                                                type_defs.BREAKPOINT_MODIFY.ENABLE_DELETE),
            delete_breakpoint: lambda: GDB_Engine.delete_breakpoint(current_address),
            refresh: self.refresh
        }
        try:
            actions[action]()
        except KeyError:
            pass
        if action != -1 and action is not None:
            self.refresh_all()

    def refresh_all(self):
        self.parent().refresh_hex_view()
        self.parent().refresh_disassemble_view()
        self.refresh()

    def tableWidget_BreakpointInfo_double_clicked(self, index):
        current_address_text = self.tableWidget_BreakpointInfo.item(index.row(), Break.ADDR_COL).text()
        current_address = SysUtils.extract_address(current_address_text)
        current_address_int = int(current_address, 16)

        if index.column() == Break.COND_COL:
            self.parent().add_breakpoint_condition(current_address_int)
            self.refresh_all()
        else:
            current_breakpoint_type = self.tableWidget_BreakpointInfo.item(index.row(), Break.TYPE_COL).text()
            if "breakpoint" in current_breakpoint_type:
                self.parent().disassemble_expression(current_address, append_to_travel_history=True)
            else:
                self.parent().hex_dump_address(current_address_int)

    def closeEvent(self, QCloseEvent):

        instances.remove(self)


class TrackWatchpointWidgetForm(QWidget, TrackWatchpointWidget):
    def __init__(self, address, length, watchpoint_type, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center(self)
        self.setWindowFlags(Qt.Window)
        if watchpoint_type == type_defs.WATCHPOINT_TYPE.WRITE_ONLY:
            string = "writing to"
        elif watchpoint_type == type_defs.WATCHPOINT_TYPE.READ_ONLY:
            string = "reading from"
        elif watchpoint_type == type_defs.WATCHPOINT_TYPE.BOTH:
            string = "accessing to"
        else:
            raise Exception("Watchpoint type is invalid: " + str(watchpoint_type))
        self.setWindowTitle("Opcodes " + string + " the address " + address)
        breakpoints = GDB_Engine.track_watchpoint(address, length, watchpoint_type)
        if not breakpoints:
            QMessageBox.information(self, "Error", "Unable to track watchpoint at expression " + address)
            return
        self.address = address
        self.breakpoints = breakpoints
        self.info = {}
        self.last_selected_row = 0
        self.stopped = False
        self.pushButton_Stop.clicked.connect(self.pushButton_Stop_clicked)
        self.pushButton_Refresh.clicked.connect(self.update_list)
        self.tableWidget_Opcodes.itemDoubleClicked.connect(self.tableWidget_Opcodes_item_double_clicked)
        self.tableWidget_Opcodes.selectionModel().currentChanged.connect(self.tableWidget_Opcodes_current_changed)
        self.update_timer = QTimer()
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self.update_list)
        self.update_timer.start()

    def update_list(self):
        info = GDB_Engine.get_track_watchpoint_info(self.breakpoints)
        if not info:
            return
        if self.info == info:
            return
        self.info = info
        self.tableWidget_Opcodes.setRowCount(0)
        self.tableWidget_Opcodes.setRowCount(len(info))
        for row, key in enumerate(info):
            self.tableWidget_Opcodes.setItem(row, TRACK_WATCHPOINT_COUNT_COL, QTableWidgetItem(str(info[key][0])))
            self.tableWidget_Opcodes.setItem(row, TRACK_WATCHPOINT_ADDR_COL, QTableWidgetItem(info[key][1]))
        self.tableWidget_Opcodes.resizeColumnsToContents()
        self.tableWidget_Opcodes.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_Opcodes.selectRow(self.last_selected_row)

    def tableWidget_Opcodes_current_changed(self, QModelIndex_current):
        current_row = QModelIndex_current.row()
        if current_row >= 0:
            self.last_selected_row = current_row

        info = self.info
        key_list = list(info)
        key = key_list[self.last_selected_row]
        self.textBrowser_Info.clear()
        for item in info[key][2]:
            self.textBrowser_Info.append(item + "=" + info[key][2][item])
        self.textBrowser_Info.append(" ")
        for item in info[key][3]:
            self.textBrowser_Info.append(item + "=" + info[key][3][item])
        self.textBrowser_Info.verticalScrollBar().setValue(self.textBrowser_Info.verticalScrollBar().minimum())
        self.textBrowser_Disassemble.setPlainText(info[key][4])

    def tableWidget_Opcodes_item_double_clicked(self, index):
        self.parent().memory_view_window.disassemble_expression(
            self.tableWidget_Opcodes.item(index.row(), TRACK_WATCHPOINT_ADDR_COL).text(),
            append_to_travel_history=True)
        self.parent().memory_view_window.show()
        self.parent().memory_view_window.activateWindow()

    def pushButton_Stop_clicked(self):
        if self.stopped:
            self.close()
        if not GDB_Engine.delete_breakpoint(self.address):
            QMessageBox.information(self, "Error", "Unable to delete watchpoint at expression " + self.address)
            return
        self.stopped = True
        self.pushButton_Stop.setText("Close")

    def closeEvent(self, QCloseEvent):
        if GDB_Engine.inferior_status == type_defs.INFERIOR_STATUS.INFERIOR_RUNNING:
            QCloseEvent.ignore()
            raise type_defs.InferiorRunningException
        try:
            self.update_timer.stop()
        except AttributeError:
            pass

        instances.remove(self)
        GDB_Engine.execute_func_temporary_interruption(GDB_Engine.delete_breakpoint, self.address)


class TrackBreakpointWidgetForm(QWidget, TrackBreakpointWidget):
    def __init__(self, address, instruction, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        self.setWindowFlags(Qt.Window)
        GuiUtils.center_to_parent(self)
        self.setWindowTitle("Addresses accessed by instruction '" + instruction + "'")
        label_text = "Enter the register expression(s) you want to track" \
                     "\nRegister names should start with a '$' sign" \
                     "\nEach expression should be separated with a comma" \
                     "\n\nFor instance:" \
                     "\nLet's say the instruction is 'mov [rax+rbx],30'" \
                     "\nThen you should enter '$rax+$rbx'(without quotes)" \
                     "\nSo PINCE can track address [rax+rbx]" \
                     "\n\nAnother example:" \
                     "\nIf you enter '$rax,$rbx*$rcx+4,$rbp'(without quotes)" \
                     "\nPINCE will track down addresses [rax],[rbx*rcx+4] and [rbp]"
        register_expression_dialog = InputDialogForm(item_list=[(label_text, "")])
        if register_expression_dialog.exec_():
            register_expressions = register_expression_dialog.get_values()
        else:
            return
        breakpoint = GDB_Engine.track_breakpoint(address, register_expressions)
        if not breakpoint:
            QMessageBox.information(self, "Error", "Unable to track breakpoint at expression " + address)
            return
        self.label_Info.setText("Pause the process to refresh 'Value' part of the table(" +
                                Hotkeys.pause_hotkey.value + " or " + Hotkeys.break_hotkey.value + ")")
        self.address = address
        self.breakpoint = breakpoint
        self.info = {}
        self.last_selected_row = 0
        self.stopped = False
        GuiUtils.fill_value_combobox(self.comboBox_ValueType)
        self.pushButton_Stop.clicked.connect(self.pushButton_Stop_clicked)
        self.tableWidget_TrackInfo.itemDoubleClicked.connect(self.tableWidget_TrackInfo_item_double_clicked)
        self.tableWidget_TrackInfo.selectionModel().currentChanged.connect(self.tableWidget_TrackInfo_current_changed)
        self.comboBox_ValueType.currentIndexChanged.connect(self.update_values)
        self.comboBox_ValueType.setToolTip("Allan please add details")  # planned easter egg
        self.update_timer = QTimer()
        self.update_timer.setInterval(100)
        self.update_timer.timeout.connect(self.update_list)
        self.update_timer.start()
        self.parent().process_stopped.connect(self.update_values)
        self.parent().refresh_disassemble_view()

    def update_list(self):
        info = GDB_Engine.get_track_breakpoint_info(self.breakpoint)
        if not info:
            return
        if info == self.info:
            return
        self.info = info
        self.tableWidget_TrackInfo.setRowCount(0)
        for register_expression in info:
            for row, address in enumerate(info[register_expression]):
                self.tableWidget_TrackInfo.setRowCount(self.tableWidget_TrackInfo.rowCount() + 1)
                self.tableWidget_TrackInfo.setItem(row, TRACK_BREAKPOINT_COUNT_COL,
                                                   QTableWidgetItem(str(info[register_expression][address])))
                self.tableWidget_TrackInfo.setItem(row, TRACK_BREAKPOINT_ADDR_COL, QTableWidgetItem(address))
                self.tableWidget_TrackInfo.setItem(row, TRACK_BREAKPOINT_SOURCE_COL,
                                                   QTableWidgetItem("[" + register_expression + "]"))
        self.tableWidget_TrackInfo.resizeColumnsToContents()
        self.tableWidget_TrackInfo.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_TrackInfo.selectRow(self.last_selected_row)

    def update_values(self):
        param_list = []
        value_type = self.comboBox_ValueType.currentIndex()
        for row in range(self.tableWidget_TrackInfo.rowCount()):
            address = self.tableWidget_TrackInfo.item(row, TRACK_BREAKPOINT_ADDR_COL).text()
            param_list.append((address, value_type, 10))
        value_list = GDB_Engine.read_memory_multiple(param_list)
        for row, value in enumerate(value_list):
            value = "" if value is None else str(value)
            self.tableWidget_TrackInfo.setItem(row, TRACK_BREAKPOINT_VALUE_COL, QTableWidgetItem(value))
        self.tableWidget_TrackInfo.resizeColumnsToContents()
        self.tableWidget_TrackInfo.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_TrackInfo.selectRow(self.last_selected_row)

    def tableWidget_TrackInfo_current_changed(self, QModelIndex_current):
        current_row = QModelIndex_current.row()
        if current_row >= 0:
            self.last_selected_row = current_row

    def tableWidget_TrackInfo_item_double_clicked(self, index):
        address = self.tableWidget_TrackInfo.item(index.row(), TRACK_BREAKPOINT_ADDR_COL).text()
        self.parent().parent().add_entry_to_addresstable("Accessed by " + self.address, address,
                                                         self.comboBox_ValueType.currentIndex(), 10, True)

    def pushButton_Stop_clicked(self):
        if self.stopped:
            self.close()
        if not GDB_Engine.delete_breakpoint(self.address):
            QMessageBox.information(self, "Error", "Unable to delete breakpoint at expression " + self.address)
            return
        self.stopped = True
        self.pushButton_Stop.setText("Close")
        self.parent().refresh_disassemble_view()

    def closeEvent(self, QCloseEvent):
        if GDB_Engine.inferior_status == type_defs.INFERIOR_STATUS.INFERIOR_RUNNING:
            QCloseEvent.ignore()
            raise type_defs.InferiorRunningException
        try:
            self.update_timer.stop()
        except AttributeError:
            pass

        instances.remove(self)
        GDB_Engine.execute_func_temporary_interruption(GDB_Engine.delete_breakpoint, self.address)
        self.parent().refresh_disassemble_view()


class TraceInstructionsPromptDialogForm(QDialog, TraceInstructionsPromptDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

    def get_values(self):
        max_trace_count = int(self.lineEdit_MaxTraceCount.text())
        trigger_condition = self.lineEdit_TriggerCondition.text()
        stop_condition = self.lineEdit_StopCondition.text()
        if self.checkBox_StepOver.isChecked():
            step_mode = type_defs.STEP_MODE.STEP_OVER
        else:
            step_mode = type_defs.STEP_MODE.SINGLE_STEP
        stop_after_trace = self.checkBox_StopAfterTrace.isChecked()
        collect_general_registers = self.checkBox_GeneralRegisters.isChecked()
        collect_flag_registers = self.checkBox_FlagRegisters.isChecked()
        collect_segment_registers = self.checkBox_SegmentRegisters.isChecked()
        collect_float_registers = self.checkBox_FloatRegisters.isChecked()
        return (max_trace_count, trigger_condition, stop_condition, step_mode, stop_after_trace,
                collect_general_registers, collect_flag_registers, collect_segment_registers, collect_float_registers)

    def accept(self):
        if int(self.lineEdit_MaxTraceCount.text()) >= 1:
            super(TraceInstructionsPromptDialogForm, self).accept()
        else:
            QMessageBox.information(self, "Error", "Max trace count must be greater than or equal to 1")


class TraceInstructionsWaitWidgetForm(QWidget, TraceInstructionsWaitWidget):
    widget_closed = pyqtSignal()

    def __init__(self, address, breakpoint, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.Window | Qt.FramelessWindowHint)
        GuiUtils.center(self)
        self.address = address
        self.breakpoint = breakpoint
        media_directory = SysUtils.get_media_directory()
        self.movie = QMovie(media_directory + "/TraceInstructionsWaitWidget/ajax-loader.gif", QByteArray())
        self.label_Animated.setMovie(self.movie)
        self.movie.setScaledSize(QSize(215, 100))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(100)
        self.movie.start()
        self.pushButton_Cancel.clicked.connect(self.close)
        self.status_timer = QTimer()
        self.status_timer.setInterval(30)
        self.status_timer.timeout.connect(self.change_status)
        self.status_timer.start()

    def change_status(self):
        status_info = GDB_Engine.get_trace_instructions_status(self.breakpoint)
        if status_info[0] == type_defs.TRACE_STATUS.STATUS_FINISHED or \
                status_info[0] == type_defs.TRACE_STATUS.STATUS_PROCESSING:
            self.close()
            return
        self.label_StatusText.setText(status_info[1])
        app.processEvents()

    def closeEvent(self, QCloseEvent):
        self.status_timer.stop()
        self.label_StatusText.setText("Processing the collected data")
        self.pushButton_Cancel.setVisible(False)
        self.adjustSize()
        app.processEvents()
        status_info = GDB_Engine.get_trace_instructions_status(self.breakpoint)
        if status_info[0] == type_defs.TRACE_STATUS.STATUS_TRACING or \
                status_info[0] == type_defs.TRACE_STATUS.STATUS_PROCESSING:
            GDB_Engine.cancel_trace_instructions(self.breakpoint)
            while GDB_Engine.get_trace_instructions_status(self.breakpoint)[0] \
                    != type_defs.TRACE_STATUS.STATUS_FINISHED:
                sleep(0.1)
                app.processEvents()
        try:
            GDB_Engine.delete_breakpoint(self.address)
        except type_defs.InferiorRunningException:
            pass
        self.widget_closed.emit()


class TraceInstructionsWindowForm(QMainWindow, TraceInstructionsWindow):
    def __init__(self, address="", prompt_dialog=True, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center(self)
        self.address = address
        self.trace_data = None
        self.treeWidget_InstructionInfo.currentItemChanged.connect(self.display_collected_data)
        self.treeWidget_InstructionInfo.itemDoubleClicked.connect(self.treeWidget_InstructionInfo_item_double_clicked)
        self.treeWidget_InstructionInfo.contextMenuEvent = self.treeWidget_InstructionInfo_context_menu_event
        self.actionOpen.triggered.connect(self.load_file)
        self.actionSave.triggered.connect(self.save_file)
        self.splitter.setStretchFactor(0, 1)
        if not prompt_dialog:
            return
        prompt_dialog = TraceInstructionsPromptDialogForm()
        if prompt_dialog.exec_():
            params = (address,) + prompt_dialog.get_values()
            breakpoint = GDB_Engine.trace_instructions(*params)
            if not breakpoint:
                QMessageBox.information(self, "Error", "Failed to set breakpoint at address " + address)
                return
            self.breakpoint = breakpoint
            self.wait_dialog = TraceInstructionsWaitWidgetForm(address, breakpoint, self)
            self.wait_dialog.widget_closed.connect(self.show_trace_info)
            self.wait_dialog.show()

    def display_collected_data(self, QTreeWidgetItem_current):
        self.textBrowser_RegisterInfo.clear()
        current_dict = QTreeWidgetItem_current.trace_data[1]
        if current_dict:
            for key in current_dict:
                self.textBrowser_RegisterInfo.append(str(key) + " = " + str(current_dict[key]))
            self.textBrowser_RegisterInfo.verticalScrollBar().setValue(
                self.textBrowser_RegisterInfo.verticalScrollBar().minimum())

    def show_trace_info(self, trace_data=None):
        self.treeWidget_InstructionInfo.setStyleSheet("QTreeWidget::item{ height: 16px; }")
        parent = QTreeWidgetItem(self.treeWidget_InstructionInfo)
        self.treeWidget_InstructionInfo.setRootIndex(self.treeWidget_InstructionInfo.indexFromItem(parent))
        if trace_data:
            trace_tree, current_root_index = trace_data
        else:
            trace_data = GDB_Engine.get_trace_instructions_info(self.breakpoint)
            if trace_data:
                trace_tree, current_root_index = trace_data
            else:
                return
        self.trace_data = copy.deepcopy(trace_data)
        while current_root_index is not None:
            try:
                current_index = trace_tree[current_root_index][2][0]  # Get the first child
                current_item = trace_tree[current_index][0]
                del trace_tree[current_root_index][2][0]  # Delete it
            except IndexError:  # We've depleted the children
                current_root_index = trace_tree[current_root_index][1]  # traverse upwards
                parent = parent.parent()
                continue
            child = QTreeWidgetItem(parent)
            child.trace_data = current_item
            child.setText(0, current_item[0])
            if trace_tree[current_index][2]:  # If current item has children, traverse them
                current_root_index = current_index  # traverse downwards
                parent = child
        self.treeWidget_InstructionInfo.expandAll()

    def save_file(self):
        trace_file_path = SysUtils.get_user_path(type_defs.USER_PATHS.TRACE_INSTRUCTIONS_PATH)
        file_path = QFileDialog.getSaveFileName(self, "Save trace file", trace_file_path,
                                                "Trace File (*.trace);;All Files (*)")[0]
        if file_path:
            file_path = SysUtils.append_file_extension(file_path, "trace")
            if not SysUtils.save_file(self.trace_data, file_path):
                QMessageBox.information(self, "Error", "Cannot save to file")

    def load_file(self):
        trace_file_path = SysUtils.get_user_path(type_defs.USER_PATHS.TRACE_INSTRUCTIONS_PATH)
        file_path = QFileDialog.getOpenFileName(self, "Open trace file", trace_file_path,
                                                "Trace File (*.trace);;All Files (*)")[0]
        if file_path:
            content = SysUtils.load_file(file_path)
            if content is None:
                QMessageBox.information(self, "Error", "File " + file_path + " does not exist, " +
                                        "is inaccessible or contains invalid content. Terminating...")
                return
            self.treeWidget_InstructionInfo.clear()
            self.show_trace_info(content)

    def treeWidget_InstructionInfo_context_menu_event(self, event):
        menu = QMenu()
        expand_all = menu.addAction("Expand All")
        collapse_all = menu.addAction("Collapse All")
        font_size = self.treeWidget_InstructionInfo.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            expand_all: self.treeWidget_InstructionInfo.expandAll,
            collapse_all: self.treeWidget_InstructionInfo.collapseAll
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def treeWidget_InstructionInfo_item_double_clicked(self, index):
        current_item = GuiUtils.get_current_item(self.treeWidget_InstructionInfo)
        if not current_item:
            return
        address = SysUtils.extract_address(current_item.trace_data[0])
        if address:
            self.parent().disassemble_expression(address, append_to_travel_history=True)

    def closeEvent(self, QCloseEvent):

        instances.remove(self)


class FunctionsInfoWidgetForm(QWidget, FunctionsInfoWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center(self)
        self.setWindowFlags(Qt.Window)
        self.textBrowser_AddressInfo.setFixedHeight(100)
        self.pushButton_Search.clicked.connect(self.refresh_table)
        self.shortcut_search = QShortcut(QKeySequence("Return"), self)
        self.shortcut_search.activated.connect(self.refresh_table)
        self.tableWidget_SymbolInfo.selectionModel().currentChanged.connect(self.tableWidget_SymbolInfo_current_changed)
        self.tableWidget_SymbolInfo.itemDoubleClicked.connect(self.tableWidget_SymbolInfo_item_double_clicked)
        self.tableWidget_SymbolInfo.contextMenuEvent = self.tableWidget_SymbolInfo_context_menu_event
        icons_directory = GuiUtils.get_icons_directory()
        self.pushButton_Help.setIcon(QIcon(QPixmap(icons_directory + "/help.png")))
        self.pushButton_Help.clicked.connect(self.pushButton_Help_clicked)

    def refresh_table(self):
        input_text = self.lineEdit_SearchInput.text()
        case_sensitive = self.checkBox_CaseSensitive.isChecked()
        self.loading_dialog = LoadingDialogForm(self)
        self.background_thread = self.loading_dialog.background_thread
        self.background_thread.overrided_func = lambda: self.process_data(input_text, case_sensitive)
        self.background_thread.output_ready.connect(self.apply_data)
        self.loading_dialog.exec_()

    def process_data(self, gdb_input, case_sensitive):
        return GDB_Engine.search_functions(gdb_input, case_sensitive)

    def apply_data(self, output):
        self.tableWidget_SymbolInfo.setSortingEnabled(False)
        self.tableWidget_SymbolInfo.setRowCount(0)
        self.tableWidget_SymbolInfo.setRowCount(len(output))
        for row, item in enumerate(output):
            address = item[0]
            if address:
                address_item = QTableWidgetItem(address)
            else:
                address_item = QTableWidgetItem("DEFINED")
                address_item.setBackground(Qt.green)
            self.tableWidget_SymbolInfo.setItem(row, FUNCTIONS_INFO_ADDR_COL, address_item)
            self.tableWidget_SymbolInfo.setItem(row, FUNCTIONS_INFO_SYMBOL_COL, QTableWidgetItem(item[1]))
        self.tableWidget_SymbolInfo.setSortingEnabled(True)
        self.tableWidget_SymbolInfo.resizeColumnsToContents()
        self.tableWidget_SymbolInfo.horizontalHeader().setStretchLastSection(True)

    def tableWidget_SymbolInfo_current_changed(self, QModelIndex_current):
        self.textBrowser_AddressInfo.clear()
        address = self.tableWidget_SymbolInfo.item(QModelIndex_current.row(), FUNCTIONS_INFO_ADDR_COL).text()
        if SysUtils.extract_address(address):
            symbol = self.tableWidget_SymbolInfo.item(QModelIndex_current.row(), FUNCTIONS_INFO_SYMBOL_COL).text()
            for item in SysUtils.split_symbol(symbol):
                info = GDB_Engine.get_symbol_info(item)
                self.textBrowser_AddressInfo.append(info)
        else:
            text = "This symbol is defined. You can use its body as a gdb expression. For instance:\n\n" \
                   "void func(param) can be used as 'func' as a gdb expression"
            self.textBrowser_AddressInfo.append(text)

    def tableWidget_SymbolInfo_context_menu_event(self, event):
        def copy_to_clipboard(row, column):
            app.clipboard().setText(self.tableWidget_SymbolInfo.item(row, column).text())

        selected_row = GuiUtils.get_current_row(self.tableWidget_SymbolInfo)

        menu = QMenu()
        copy_address = menu.addAction("Copy Address")
        copy_symbol = menu.addAction("Copy Symbol")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [copy_address, copy_symbol])
        font_size = self.tableWidget_SymbolInfo.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            copy_address: lambda: copy_to_clipboard(selected_row, FUNCTIONS_INFO_ADDR_COL),
            copy_symbol: lambda: copy_to_clipboard(selected_row, FUNCTIONS_INFO_SYMBOL_COL)
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def tableWidget_SymbolInfo_item_double_clicked(self, index):
        address = self.tableWidget_SymbolInfo.item(index.row(), FUNCTIONS_INFO_ADDR_COL).text()
        self.parent().disassemble_expression(address, append_to_travel_history=True)

    def pushButton_Help_clicked(self):
        text = "\tHere's some useful regex tips:" \
               "\n'^string' searches for everything that starts with 'string'" \
               "\n'[ab]cd' searches for both 'acd' and 'bcd'" \
               "\n\n\tHow to interpret symbols:" \
               "\nA symbol that looks like 'func(param)@plt' consists of 3 pieces" \
               "\nfunc, func(param), func(param)@plt" \
               "\nThese 3 functions will have different addresses" \
               "\n@plt means this function is a subroutine for the original one" \
               "\nThere can be more than one of the same function" \
               "\nIt means that the function is overloaded"
        InputDialogForm(item_list=[(text, None, Qt.AlignLeft)], buttons=[QDialogButtonBox.Ok]).exec_()

    def closeEvent(self, QCloseEvent):

        instances.remove(self)


class HexEditDialogForm(QDialog, HexEditDialog):
    def __init__(self, address, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.lineEdit_Length.setValidator(QHexValidator(999, self))
        self.lineEdit_Address.setText(address)
        self.lineEdit_Length.setText("20")
        self.refresh_view()
        self.lineEdit_AsciiView.selectionChanged.connect(self.lineEdit_AsciiView_selection_changed)

        # TODO: Implement this
        # self.lineEdit_HexView.selectionChanged.connect(self.lineEdit_HexView_selection_changed)
        self.lineEdit_HexView.textEdited.connect(self.lineEdit_HexView_text_edited)
        self.lineEdit_AsciiView.textEdited.connect(self.lineEdit_AsciiView_text_edited)
        self.pushButton_Refresh.pressed.connect(self.refresh_view)
        self.lineEdit_Address.textChanged.connect(self.refresh_view)
        self.lineEdit_Length.textChanged.connect(self.refresh_view)

    def lineEdit_AsciiView_selection_changed(self):
        length = len(SysUtils.str_to_aob(self.lineEdit_AsciiView.selectedText(), "utf-8"))
        start_index = self.lineEdit_AsciiView.selectionStart()
        start_index = len(SysUtils.str_to_aob(self.lineEdit_AsciiView.text()[0:start_index], "utf-8"))
        if start_index > 0:
            start_index += 1
        self.lineEdit_HexView.deselect()
        self.lineEdit_HexView.setSelection(start_index, length)

    def lineEdit_HexView_selection_changed(self):
        # TODO: Implement this
        print("TODO: Implement selectionChanged signal of lineEdit_HexView")
        raise NotImplementedError

    def lineEdit_HexView_text_edited(self):
        aob_string = self.lineEdit_HexView.text()
        if not SysUtils.parse_string(aob_string, type_defs.VALUE_INDEX.INDEX_AOB):
            self.lineEdit_HexView.setStyleSheet("QLineEdit {background-color: red;}")
            return
        aob_array = aob_string.split()
        try:
            self.lineEdit_AsciiView.setText(SysUtils.aob_to_str(aob_array, "utf-8"))
            self.lineEdit_HexView.setStyleSheet("QLineEdit {background-color: white;}")
        except ValueError:
            self.lineEdit_HexView.setStyleSheet("QLineEdit {background-color: red;}")

    def lineEdit_AsciiView_text_edited(self):
        ascii_str = self.lineEdit_AsciiView.text()
        try:
            self.lineEdit_HexView.setText(SysUtils.str_to_aob(ascii_str, "utf-8"))
            self.lineEdit_AsciiView.setStyleSheet("QLineEdit {background-color: white;}")
        except ValueError:
            self.lineEdit_AsciiView.setStyleSheet("QLineEdit {background-color: red;}")

    def refresh_view(self):
        self.lineEdit_AsciiView.clear()
        self.lineEdit_HexView.clear()
        address = GDB_Engine.examine_expression(self.lineEdit_Address.text()).address
        if not address:
            return
        length = self.lineEdit_Length.text()
        try:
            length = int(length, 0)
            address = int(address, 0)
        except ValueError:
            return
        aob_array = GDB_Engine.hex_dump(address, length)
        ascii_str = SysUtils.aob_to_str(aob_array, "utf-8")
        self.lineEdit_AsciiView.setText(ascii_str)
        self.lineEdit_HexView.setText(" ".join(aob_array))

    def accept(self):
        expression = self.lineEdit_Address.text()
        address = GDB_Engine.examine_expression(expression).address
        if not address:
            QMessageBox.information(self, "Error", expression + " isn't a valid expression")
            return
        value = self.lineEdit_HexView.text()
        GDB_Engine.write_memory(address, type_defs.VALUE_INDEX.INDEX_AOB, value)
        super(HexEditDialogForm, self).accept()


class LibPINCEReferenceWidgetForm(QWidget, LibPINCEReferenceWidget):
    def convert_to_modules(self, module_strings):
        return [eval(item) for item in module_strings]

    def __init__(self, is_window=False, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.found_count = 0
        self.current_found = 0

        instances.append(self)
        if is_window:
            GuiUtils.center(self)
            self.setWindowFlags(Qt.Window)
        self.show_type_defs()
        self.splitter.setStretchFactor(0, 1)
        self.widget_Resources.resize(700, self.widget_Resources.height())
        libPINCE_directory = SysUtils.get_libpince_directory()
        self.textBrowser_TypeDefs.setText(open(libPINCE_directory + "/type_defs.py").read())
        source_menu_items = ["(Tagged only)", "(All)"]
        self.libPINCE_source_files = ["GDB_Engine", "SysUtils", "GuiUtils"]
        source_menu_items.extend(self.libPINCE_source_files)
        self.comboBox_SourceFile.addItems(source_menu_items)
        self.comboBox_SourceFile.setCurrentIndex(0)
        self.fill_resource_tree()
        icons_directory = GuiUtils.get_icons_directory()
        self.pushButton_TextUp.setIcon(QIcon(QPixmap(icons_directory + "/bullet_arrow_up.png")))
        self.pushButton_TextDown.setIcon(QIcon(QPixmap(icons_directory + "/bullet_arrow_down.png")))
        self.comboBox_SourceFile.currentIndexChanged.connect(self.comboBox_SourceFile_current_index_changed)
        self.pushButton_ShowTypeDefs.clicked.connect(self.toggle_type_defs)
        self.lineEdit_SearchText.textChanged.connect(self.highlight_text)
        self.pushButton_TextDown.clicked.connect(self.pushButton_TextDown_clicked)
        self.pushButton_TextUp.clicked.connect(self.pushButton_TextUp_clicked)
        self.lineEdit_Search.textChanged.connect(self.comboBox_SourceFile_current_index_changed)
        self.tableWidget_ResourceTable.contextMenuEvent = self.tableWidget_ResourceTable_context_menu_event
        self.treeWidget_ResourceTree.contextMenuEvent = self.treeWidget_ResourceTree_context_menu_event
        self.treeWidget_ResourceTree.expanded.connect(self.resize_resource_tree)
        self.treeWidget_ResourceTree.collapsed.connect(self.resize_resource_tree)

    def tableWidget_ResourceTable_context_menu_event(self, event):
        def copy_to_clipboard(row, column):
            app.clipboard().setText(self.tableWidget_ResourceTable.item(row, column).text())

        selected_row = GuiUtils.get_current_row(self.tableWidget_ResourceTable)

        menu = QMenu()
        refresh = menu.addAction("Refresh")
        menu.addSeparator()
        copy_item = menu.addAction("Copy Item")
        copy_value = menu.addAction("Copy Value")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [copy_item, copy_value])
        font_size = self.tableWidget_ResourceTable.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            refresh: self.fill_resource_table,
            copy_item: lambda: copy_to_clipboard(selected_row, LIBPINCE_REFERENCE_ITEM_COL),
            copy_value: lambda: copy_to_clipboard(selected_row, LIBPINCE_REFERENCE_VALUE_COL)
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def treeWidget_ResourceTree_context_menu_event(self, event):
        def copy_to_clipboard(column):
            current_item = GuiUtils.get_current_item(self.treeWidget_ResourceTree)
            if current_item:
                app.clipboard().setText(current_item.text(column))

        def expand_all():
            self.treeWidget_ResourceTree.expandAll()
            self.resize_resource_tree()

        def collapse_all():
            self.treeWidget_ResourceTree.collapseAll()
            self.resize_resource_tree()

        selected_row = GuiUtils.get_current_row(self.treeWidget_ResourceTree)

        menu = QMenu()
        refresh = menu.addAction("Refresh")
        menu.addSeparator()
        copy_item = menu.addAction("Copy Item")
        copy_value = menu.addAction("Copy Value")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [copy_item, copy_value])
        menu.addSeparator()
        expand_all_items = menu.addAction("Expand All")
        collapse_all_items = menu.addAction("Collapse All")
        font_size = self.treeWidget_ResourceTree.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            refresh: self.fill_resource_tree,
            copy_item: lambda: copy_to_clipboard(LIBPINCE_REFERENCE_ITEM_COL),
            copy_value: lambda: copy_to_clipboard(LIBPINCE_REFERENCE_VALUE_COL),
            expand_all_items: expand_all,
            collapse_all_items: collapse_all
        }

        # Thanks QT, for this unexplainable, mind blowing bug of yours
        self.treeWidget_ResourceTree.blockSignals(True)
        try:
            actions[action]()
        except KeyError:
            pass
        self.treeWidget_ResourceTree.blockSignals(False)

    def comboBox_SourceFile_current_index_changed(self):
        if self.comboBox_SourceFile.currentIndex() == 0:  # (Tagged only)
            self.fill_resource_tree()
        else:
            self.fill_resource_table()

    def resize_resource_tree(self):
        self.treeWidget_ResourceTree.resizeColumnToContents(LIBPINCE_REFERENCE_ITEM_COL)

    def fill_resource_tree(self):
        self.treeWidget_ResourceTree.setStyleSheet("QTreeWidget::item{ height: 16px; }")
        self.stackedWidget_Resources.setCurrentIndex(0)
        self.treeWidget_ResourceTree.clear()
        parent = self.treeWidget_ResourceTree
        checked_source_files = self.convert_to_modules(self.libPINCE_source_files)
        tag_dict = SysUtils.get_tags(checked_source_files, type_defs.tag_to_string, self.lineEdit_Search.text())
        docstring_dict = SysUtils.get_docstrings(checked_source_files, self.lineEdit_Search.text())
        for tag in tag_dict:
            child = QTreeWidgetItem(parent)
            child.setText(0, tag)
            for item in tag_dict[tag]:
                docstring = docstring_dict.get(item)
                docstr_child = QTreeWidgetItem(child)
                docstr_child.setText(LIBPINCE_REFERENCE_ITEM_COL, item)
                docstr_child.setText(LIBPINCE_REFERENCE_VALUE_COL, str(eval(item)))
                docstr_child.setToolTip(LIBPINCE_REFERENCE_ITEM_COL, docstring)
                docstr_child.setToolTip(LIBPINCE_REFERENCE_VALUE_COL, docstring)

        # Magic and mystery
        self.treeWidget_ResourceTree.blockSignals(True)
        if self.lineEdit_Search.text():
            self.treeWidget_ResourceTree.expandAll()
        self.resize_resource_tree()
        self.treeWidget_ResourceTree.blockSignals(False)

    def fill_resource_table(self):
        self.stackedWidget_Resources.setCurrentIndex(1)
        self.tableWidget_ResourceTable.setSortingEnabled(False)
        self.tableWidget_ResourceTable.setRowCount(0)
        if self.comboBox_SourceFile.currentIndex() == 1:  # (All)
            checked_source_files = self.libPINCE_source_files
        else:
            checked_source_files = [self.comboBox_SourceFile.currentText()]
        checked_source_files = self.convert_to_modules(checked_source_files)
        element_dict = SysUtils.get_docstrings(checked_source_files, self.lineEdit_Search.text())
        self.tableWidget_ResourceTable.setRowCount(len(element_dict))
        for row, item in enumerate(element_dict):
            docstring = element_dict.get(item)
            table_widget_item = QTableWidgetItem(item)
            table_widget_item_value = QTableWidgetItem(str(eval(item)))
            table_widget_item.setToolTip(docstring)
            table_widget_item_value.setToolTip(docstring)
            self.tableWidget_ResourceTable.setItem(row, LIBPINCE_REFERENCE_ITEM_COL, table_widget_item)
            self.tableWidget_ResourceTable.setItem(row, LIBPINCE_REFERENCE_VALUE_COL, table_widget_item_value)
        self.tableWidget_ResourceTable.setSortingEnabled(True)
        self.tableWidget_ResourceTable.sortByColumn(LIBPINCE_REFERENCE_ITEM_COL, Qt.AscendingOrder)
        self.tableWidget_ResourceTable.resizeColumnsToContents()
        self.tableWidget_ResourceTable.horizontalHeader().setStretchLastSection(True)

    def pushButton_TextDown_clicked(self):
        if self.found_count == 0:
            return
        cursor = self.textBrowser_TypeDefs.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.Start)
        self.textBrowser_TypeDefs.setTextCursor(cursor)
        if self.current_found == self.found_count:
            self.current_found = 1
        else:
            self.current_found += 1
        pattern = self.lineEdit_SearchText.text()
        for x in range(self.current_found):
            self.textBrowser_TypeDefs.find(pattern)
        self.label_FoundCount.setText(str(self.current_found) + "/" + str(self.found_count))

    def pushButton_TextUp_clicked(self):
        if self.found_count == 0:
            return
        cursor = self.textBrowser_TypeDefs.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.Start)
        self.textBrowser_TypeDefs.setTextCursor(cursor)
        if self.current_found == 1:
            self.current_found = self.found_count
        else:
            self.current_found -= 1
        pattern = self.lineEdit_SearchText.text()
        for x in range(self.current_found):
            self.textBrowser_TypeDefs.find(pattern)
        self.label_FoundCount.setText(str(self.current_found) + "/" + str(self.found_count))

    def highlight_text(self):
        self.textBrowser_TypeDefs.selectAll()
        self.textBrowser_TypeDefs.setTextBackgroundColor(QColor("white"))
        cursor = self.textBrowser_TypeDefs.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.Start)
        self.textBrowser_TypeDefs.setTextCursor(cursor)

        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QBrush(QColor("red")))
        pattern = self.lineEdit_SearchText.text()
        found_count = 0
        while True:
            if not self.textBrowser_TypeDefs.find(pattern):
                break
            cursor = self.textBrowser_TypeDefs.textCursor()
            cursor.mergeCharFormat(highlight_format)
            found_count += 1
        self.found_count = found_count
        if found_count == 0:
            self.label_FoundCount.setText("0/0")
            return
        cursor = self.textBrowser_TypeDefs.textCursor()
        cursor.clearSelection()
        cursor.movePosition(QTextCursor.Start)
        self.textBrowser_TypeDefs.setTextCursor(cursor)
        self.textBrowser_TypeDefs.find(pattern)
        self.current_found = 1
        self.label_FoundCount.setText("1/" + str(found_count))

    def toggle_type_defs(self):
        if self.type_defs_shown:
            self.hide_type_defs()
        else:
            self.show_type_defs()

    def hide_type_defs(self):
        self.type_defs_shown = False
        self.widget_TypeDefs.hide()
        self.pushButton_ShowTypeDefs.setText("Show type_defs")

    def show_type_defs(self):
        self.type_defs_shown = True
        self.widget_TypeDefs.show()
        self.pushButton_ShowTypeDefs.setText("Hide type_defs")

    def closeEvent(self, QCloseEvent):

        instances.remove(self)


class LogFileWidgetForm(QWidget, LogFileWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        GuiUtils.center(self)

        instances.append(self)
        self.setWindowFlags(Qt.Window)
        self.contents = ""
        self.refresh_contents()
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(500)
        self.refresh_timer.timeout.connect(self.refresh_contents)
        self.refresh_timer.start()

    def refresh_contents(self):
        log_path = SysUtils.get_logging_file(GDB_Engine.currentpid)
        self.setWindowTitle("Log File of PID " + str(GDB_Engine.currentpid))
        self.label_FilePath.setText("Contents of " + log_path + " (only last 20000 bytes are shown)")
        logging_status = "<font color=blue>ON</font>" if gdb_logging else "<font color=red>OFF</font>"
        self.label_LoggingStatus.setText("<b>LOGGING: " + logging_status + "</b>")
        try:
            log_file = open(log_path)
        except OSError:
            self.textBrowser_LogContent.clear()
            error_message = "Unable to read log file at " + log_path + "\n"
            if not gdb_logging:
                error_message += "Go to Settings->Debug to enable logging"
            self.textBrowser_LogContent.setText(error_message)
            return
        log_file.seek(0, io.SEEK_END)
        end_pos = log_file.tell()
        if end_pos > 20000:
            log_file.seek(end_pos - 20000, io.SEEK_SET)
        else:
            log_file.seek(0, io.SEEK_SET)
        contents = log_file.read().split("\n", 1)[-1]
        if contents != self.contents:
            self.contents = contents
            self.textBrowser_LogContent.clear()
            self.textBrowser_LogContent.setPlainText(contents)

            # Scrolling to bottom
            cursor = self.textBrowser_LogContent.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.textBrowser_LogContent.setTextCursor(cursor)
            self.textBrowser_LogContent.ensureCursorVisible()
        log_file.close()

    def closeEvent(self, QCloseEvent):

        instances.remove(self)
        self.refresh_timer.stop()


class SearchOpcodeWidgetForm(QWidget, SearchOpcodeWidget):
    def __init__(self, start="", end="", parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center(self)
        self.setWindowFlags(Qt.Window)
        self.lineEdit_Start.setText(start)
        self.lineEdit_End.setText(end)
        self.tableWidget_Opcodes.setColumnWidth(SEARCH_OPCODE_ADDR_COL, 250)
        icons_directory = GuiUtils.get_icons_directory()
        self.pushButton_Help.setIcon(QIcon(QPixmap(icons_directory + "/help.png")))
        self.pushButton_Help.clicked.connect(self.pushButton_Help_clicked)
        self.pushButton_Search.clicked.connect(self.refresh_table)
        self.shortcut_search = QShortcut(QKeySequence("Return"), self)
        self.shortcut_search.activated.connect(self.refresh_table)
        self.tableWidget_Opcodes.itemDoubleClicked.connect(self.tableWidget_Opcodes_item_double_clicked)
        self.tableWidget_Opcodes.contextMenuEvent = self.tableWidget_Opcodes_context_menu_event

    def refresh_table(self):
        start_address = self.lineEdit_Start.text()
        end_address = self.lineEdit_End.text()
        regex = self.lineEdit_Regex.text()
        case_sensitive = self.checkBox_CaseSensitive.isChecked()
        enable_regex = self.checkBox_Regex.isChecked()
        self.loading_dialog = LoadingDialogForm(self)
        self.background_thread = self.loading_dialog.background_thread
        self.background_thread.overrided_func = lambda: self.process_data(regex, start_address, end_address,
                                                                          case_sensitive, enable_regex)
        self.background_thread.output_ready.connect(self.apply_data)
        self.loading_dialog.exec_()

    def process_data(self, regex, start_address, end_address, case_sensitive, enable_regex):
        return GDB_Engine.search_opcode(regex, start_address, end_address, case_sensitive, enable_regex)

    def apply_data(self, disas_data):
        if disas_data is None:
            QMessageBox.information(self, "Error", "Given regex isn't valid, check terminal to see the error")
            return
        self.tableWidget_Opcodes.setSortingEnabled(False)
        self.tableWidget_Opcodes.setRowCount(0)
        self.tableWidget_Opcodes.setRowCount(len(disas_data))
        for row, item in enumerate(disas_data):
            self.tableWidget_Opcodes.setItem(row, SEARCH_OPCODE_ADDR_COL, QTableWidgetItem(item[0]))
            self.tableWidget_Opcodes.setItem(row, SEARCH_OPCODE_OPCODES_COL, QTableWidgetItem(item[1]))
        self.tableWidget_Opcodes.setSortingEnabled(True)

    def pushButton_Help_clicked(self):
        text = "\tHere's some useful regex examples:" \
               "\n'call|rax' searches for opcodes that contain 'call' or 'rax'" \
               "\n'[re]cx' searches for both 'rcx' and 'ecx'" \
               "\nUse the char '\\' to escape special chars such as '['" \
               "\n'\[rsp\]' searches for opcodes that contain '[rsp]'"
        InputDialogForm(item_list=[(text, None, Qt.AlignLeft)], buttons=[QDialogButtonBox.Ok]).exec_()

    def tableWidget_Opcodes_item_double_clicked(self, index):
        row = index.row()
        address = self.tableWidget_Opcodes.item(row, SEARCH_OPCODE_ADDR_COL).text()
        self.parent().disassemble_expression(SysUtils.extract_address(address), append_to_travel_history=True)

    def tableWidget_Opcodes_context_menu_event(self, event):
        def copy_to_clipboard(row, column):
            app.clipboard().setText(self.tableWidget_Opcodes.item(row, column).text())

        selected_row = GuiUtils.get_current_row(self.tableWidget_Opcodes)

        menu = QMenu()
        copy_address = menu.addAction("Copy Address")
        copy_opcode = menu.addAction("Copy Opcode")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [copy_address, copy_opcode])
        font_size = self.tableWidget_Opcodes.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            copy_address: lambda: copy_to_clipboard(selected_row, SEARCH_OPCODE_ADDR_COL),
            copy_opcode: lambda: copy_to_clipboard(selected_row, SEARCH_OPCODE_OPCODES_COL)
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def closeEvent(self, QCloseEvent):

        instances.remove(self)


class MemoryRegionsWidgetForm(QWidget, MemoryRegionsWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center(self)
        self.setWindowFlags(Qt.Window)
        self.refresh_table()
        self.tableWidget_MemoryRegions.contextMenuEvent = self.tableWidget_MemoryRegions_context_menu_event
        self.tableWidget_MemoryRegions.itemDoubleClicked.connect(self.tableWidget_MemoryRegions_item_double_clicked)
        self.shortcut_refresh = QShortcut(QKeySequence("R"), self)
        self.shortcut_refresh.activated.connect(self.refresh_table)

    def refresh_table(self):
        memory_regions = SysUtils.get_memory_regions(GDB_Engine.currentpid)
        self.tableWidget_MemoryRegions.setRowCount(0)
        self.tableWidget_MemoryRegions.setRowCount(len(memory_regions))
        for row, region in enumerate(memory_regions):
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_ADDR_COL, QTableWidgetItem(region.addr))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_PERM_COL, QTableWidgetItem(region.perms))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_SIZE_COL, QTableWidgetItem(hex(region.size)))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_PATH_COL, QTableWidgetItem(region.path))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_RSS_COL, QTableWidgetItem(hex(region.rss)))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_PSS_COL, QTableWidgetItem(hex(region.pss)))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_SHRCLN_COL,
                                                   QTableWidgetItem(hex(region.shared_clean)))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_SHRDRTY_COL,
                                                   QTableWidgetItem(hex(region.shared_dirty)))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_PRIVCLN_COL,
                                                   QTableWidgetItem(hex(region.private_clean)))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_PRIVDRTY_COL,
                                                   QTableWidgetItem(hex(region.private_dirty)))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_REF_COL,
                                                   QTableWidgetItem(hex(region.referenced)))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_ANON_COL,
                                                   QTableWidgetItem(hex(region.anonymous)))
            self.tableWidget_MemoryRegions.setItem(row, MEMORY_REGIONS_SWAP_COL, QTableWidgetItem(hex(region.swap)))
        self.tableWidget_MemoryRegions.resizeColumnsToContents()
        self.tableWidget_MemoryRegions.horizontalHeader().setStretchLastSection(True)

    def tableWidget_MemoryRegions_context_menu_event(self, event):
        def copy_to_clipboard(row, column):
            app.clipboard().setText(self.tableWidget_MemoryRegions.item(row, column).text())

        selected_row = GuiUtils.get_current_row(self.tableWidget_MemoryRegions)

        menu = QMenu()
        refresh = menu.addAction("Refresh[R]")
        menu.addSeparator()
        copy_addresses = menu.addAction("Copy Addresses")
        copy_size = menu.addAction("Copy Size")
        copy_path = menu.addAction("Copy Path")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [copy_addresses, copy_size, copy_path])
        font_size = self.tableWidget_MemoryRegions.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            refresh: self.refresh_table,
            copy_addresses: lambda: copy_to_clipboard(selected_row, MEMORY_REGIONS_ADDR_COL),
            copy_size: lambda: copy_to_clipboard(selected_row, MEMORY_REGIONS_SIZE_COL),
            copy_path: lambda: copy_to_clipboard(selected_row, MEMORY_REGIONS_PATH_COL)
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def tableWidget_MemoryRegions_item_double_clicked(self, index):
        row = index.row()
        address = self.tableWidget_MemoryRegions.item(row, MEMORY_REGIONS_ADDR_COL).text()
        address_int = int(address.split("-")[0], 16)
        self.parent().hex_dump_address(address_int)

    def closeEvent(self, QCloseEvent):

        instances.remove(self)


class ReferencedStringsWidgetForm(QWidget, ReferencedStringsWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        GuiUtils.fill_value_combobox(self.comboBox_ValueType, type_defs.VALUE_INDEX.INDEX_STRING_UTF8)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center_to_parent(self)
        self.setWindowFlags(Qt.Window)
        self.tableWidget_References.setColumnWidth(REF_STR_ADDR_COL, 150)
        self.tableWidget_References.setColumnWidth(REF_STR_COUNT_COL, 80)
        self.splitter.setStretchFactor(0, 1)
        self.listWidget_Referrers.resize(400, self.listWidget_Referrers.height())
        self.hex_len = 16 if GDB_Engine.inferior_arch == type_defs.INFERIOR_ARCH.ARCH_64 else 8
        str_dict, jmp_dict, call_dict = GDB_Engine.get_dissect_code_data()
        if len(str_dict) == 0 and len(jmp_dict) == 0 and len(call_dict) == 0:
            confirm_dialog = InputDialogForm(item_list=[("You need to dissect code first\nProceed?",)])
            if confirm_dialog.exec_():
                dissect_code_dialog = DissectCodeDialogForm()
                dissect_code_dialog.scan_finished_signal.connect(dissect_code_dialog.accept)
                dissect_code_dialog.exec_()
        str_dict.close()
        jmp_dict.close()
        call_dict.close()
        self.refresh_table()
        self.tableWidget_References.sortByColumn(REF_STR_ADDR_COL, Qt.AscendingOrder)
        self.tableWidget_References.selectionModel().currentChanged.connect(self.tableWidget_References_current_changed)
        self.listWidget_Referrers.itemDoubleClicked.connect(self.listWidget_Referrers_item_double_clicked)
        self.tableWidget_References.itemDoubleClicked.connect(self.tableWidget_References_item_double_clicked)
        self.tableWidget_References.contextMenuEvent = self.tableWidget_References_context_menu_event
        self.listWidget_Referrers.contextMenuEvent = self.listWidget_Referrers_context_menu_event
        self.pushButton_Search.clicked.connect(self.refresh_table)
        self.comboBox_ValueType.currentIndexChanged.connect(self.refresh_table)
        self.shortcut_search = QShortcut(QKeySequence("Return"), self)
        self.shortcut_search.activated.connect(self.refresh_table)

    def pad_hex(self, hex_str):
        index = hex_str.find(" ")
        if index == -1:
            self_len = 0
        else:
            self_len = len(hex_str) - index
        return '0x' + hex_str[2:].zfill(self.hex_len + self_len)

    def refresh_table(self):
        item_list = GDB_Engine.search_referenced_strings(self.lineEdit_Regex.text(),
                                                         self.comboBox_ValueType.currentIndex(),
                                                         self.checkBox_CaseSensitive.isChecked(),
                                                         self.checkBox_Regex.isChecked())
        if item_list is None:
            QMessageBox.information(self, "Error",
                                    "An exception occurred while trying to compile the given regex\n")
            return
        self.tableWidget_References.setSortingEnabled(False)
        self.tableWidget_References.setRowCount(0)
        self.tableWidget_References.setRowCount(len(item_list))
        for row, item in enumerate(item_list):
            self.tableWidget_References.setItem(row, REF_STR_ADDR_COL, QTableWidgetItem(self.pad_hex(item[0])))
            table_widget_item = QTableWidgetItem()
            table_widget_item.setData(Qt.EditRole, item[1])
            self.tableWidget_References.setItem(row, REF_STR_COUNT_COL, table_widget_item)
            table_widget_item = QTableWidgetItem()
            table_widget_item.setData(Qt.EditRole, item[2])
            self.tableWidget_References.setItem(row, REF_STR_VAL_COL, table_widget_item)
        self.tableWidget_References.setSortingEnabled(True)

    def tableWidget_References_current_changed(self, QModelIndex_current):
        if QModelIndex_current.row() < 0:
            return
        self.listWidget_Referrers.clear()
        str_dict = GDB_Engine.get_dissect_code_data(True, False, False)[0]
        addr = self.tableWidget_References.item(QModelIndex_current.row(), REF_STR_ADDR_COL).text()
        referrers = str_dict[hex(int(addr, 16))]
        addrs = [hex(address) for address in referrers]
        self.listWidget_Referrers.addItems([self.pad_hex(item.all) for item in GDB_Engine.examine_expressions(addrs)])
        self.listWidget_Referrers.sortItems(Qt.AscendingOrder)
        str_dict.close()

    def tableWidget_References_item_double_clicked(self, index):
        row = index.row()
        address = self.tableWidget_References.item(row, REF_STR_ADDR_COL).text()
        self.parent().hex_dump_address(int(address, 16))

    def listWidget_Referrers_item_double_clicked(self, item):
        self.parent().disassemble_expression(SysUtils.extract_address(item.text()), append_to_travel_history=True)

    def tableWidget_References_context_menu_event(self, event):
        def copy_to_clipboard(row, column):
            app.clipboard().setText(self.tableWidget_References.item(row, column).text())

        selected_row = GuiUtils.get_current_row(self.tableWidget_References)

        menu = QMenu()
        copy_address = menu.addAction("Copy Address")
        copy_value = menu.addAction("Copy Value")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [copy_address, copy_value])
        font_size = self.tableWidget_References.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            copy_address: lambda: copy_to_clipboard(selected_row, REF_STR_ADDR_COL),
            copy_value: lambda: copy_to_clipboard(selected_row, REF_STR_VAL_COL)
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def listWidget_Referrers_context_menu_event(self, event):
        def copy_to_clipboard(row):
            app.clipboard().setText(self.listWidget_Referrers.item(row).text())

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

    def closeEvent(self, QCloseEvent):

        instances.remove(self)


class ReferencedCallsWidgetForm(QWidget, ReferencedCallsWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)
        self.parent = lambda: parent

        instances.append(self)
        GuiUtils.center_to_parent(self)
        self.setWindowFlags(Qt.Window)
        self.tableWidget_References.setColumnWidth(REF_CALL_ADDR_COL, 480)
        self.splitter.setStretchFactor(0, 1)
        self.listWidget_Referrers.resize(400, self.listWidget_Referrers.height())
        self.hex_len = 16 if GDB_Engine.inferior_arch == type_defs.INFERIOR_ARCH.ARCH_64 else 8
        str_dict, jmp_dict, call_dict = GDB_Engine.get_dissect_code_data()
        if len(str_dict) == 0 and len(jmp_dict) == 0 and len(call_dict) == 0:
            confirm_dialog = InputDialogForm(item_list=[("You need to dissect code first\nProceed?",)])
            if confirm_dialog.exec_():
                dissect_code_dialog = DissectCodeDialogForm()
                dissect_code_dialog.scan_finished_signal.connect(dissect_code_dialog.accept)
                dissect_code_dialog.exec_()
        str_dict.close()
        jmp_dict.close()
        call_dict.close()
        self.refresh_table()
        self.tableWidget_References.sortByColumn(REF_CALL_ADDR_COL, Qt.AscendingOrder)
        self.tableWidget_References.selectionModel().currentChanged.connect(self.tableWidget_References_current_changed)
        self.listWidget_Referrers.itemDoubleClicked.connect(self.listWidget_Referrers_item_double_clicked)
        self.tableWidget_References.itemDoubleClicked.connect(self.tableWidget_References_item_double_clicked)
        self.tableWidget_References.contextMenuEvent = self.tableWidget_References_context_menu_event
        self.listWidget_Referrers.contextMenuEvent = self.listWidget_Referrers_context_menu_event
        self.pushButton_Search.clicked.connect(self.refresh_table)
        self.shortcut_search = QShortcut(QKeySequence("Return"), self)
        self.shortcut_search.activated.connect(self.refresh_table)

    def pad_hex(self, hex_str):
        index = hex_str.find(" ")
        if index == -1:
            self_len = 0
        else:
            self_len = len(hex_str) - index
        return '0x' + hex_str[2:].zfill(self.hex_len + self_len)

    def refresh_table(self):
        item_list = GDB_Engine.search_referenced_calls(self.lineEdit_Regex.text(),
                                                       self.checkBox_CaseSensitive.isChecked(),
                                                       self.checkBox_Regex.isChecked())
        if item_list is None:
            QMessageBox.information(self, "Error",
                                    "An exception occurred while trying to compile the given regex\n")
            return
        self.tableWidget_References.setSortingEnabled(False)
        self.tableWidget_References.setRowCount(0)
        self.tableWidget_References.setRowCount(len(item_list))
        for row, item in enumerate(item_list):
            self.tableWidget_References.setItem(row, REF_CALL_ADDR_COL, QTableWidgetItem(self.pad_hex(item[0])))
            table_widget_item = QTableWidgetItem()
            table_widget_item.setData(Qt.EditRole, item[1])
            self.tableWidget_References.setItem(row, REF_CALL_COUNT_COL, table_widget_item)
        self.tableWidget_References.setSortingEnabled(True)

    def tableWidget_References_current_changed(self, QModelIndex_current):
        if QModelIndex_current.row() < 0:
            return
        self.listWidget_Referrers.clear()
        call_dict = GDB_Engine.get_dissect_code_data(False, False, True)[0]
        addr = self.tableWidget_References.item(QModelIndex_current.row(), REF_CALL_ADDR_COL).text()
        referrers = call_dict[hex(int(SysUtils.extract_address(addr), 16))]
        addrs = [hex(address) for address in referrers]
        self.listWidget_Referrers.addItems([self.pad_hex(item.all) for item in GDB_Engine.examine_expressions(addrs)])
        self.listWidget_Referrers.sortItems(Qt.AscendingOrder)
        call_dict.close()

    def tableWidget_References_item_double_clicked(self, index):
        row = index.row()
        address = self.tableWidget_References.item(row, REF_CALL_ADDR_COL).text()
        self.parent().disassemble_expression(SysUtils.extract_address(address), append_to_travel_history=True)

    def listWidget_Referrers_item_double_clicked(self, item):
        self.parent().disassemble_expression(SysUtils.extract_address(item.text()), append_to_travel_history=True)

    def tableWidget_References_context_menu_event(self, event):
        def copy_to_clipboard(row, column):
            app.clipboard().setText(self.tableWidget_References.item(row, column).text())

        selected_row = GuiUtils.get_current_row(self.tableWidget_References)

        menu = QMenu()
        copy_address = menu.addAction("Copy Address")
        if selected_row == -1:
            GuiUtils.delete_menu_entries(menu, [copy_address])
        font_size = self.tableWidget_References.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            copy_address: lambda: copy_to_clipboard(selected_row, REF_CALL_ADDR_COL)
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def listWidget_Referrers_context_menu_event(self, event):
        def copy_to_clipboard(row):
            app.clipboard().setText(self.listWidget_Referrers.item(row).text())

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

    def closeEvent(self, QCloseEvent):

        instances.remove(self)


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

    def pad_hex(self, hex_str):
        index = hex_str.find(" ")
        if index == -1:
            self_len = 0
        else:
            self_len = len(hex_str) - index
        return '0x' + hex_str[2:].zfill(self.hex_len + self_len)

    def collect_referrer_data(self):
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

    def refresh_table(self):
        searched_str = self.lineEdit_Regex.text()
        case_sensitive = self.checkBox_CaseSensitive.isChecked()
        enable_regex = self.checkBox_Regex.isChecked()
        if enable_regex:
            try:
                if case_sensitive:
                    regex = re.compile(searched_str)
                else:
                    regex = re.compile(searched_str, re.IGNORECASE)
            except:
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

    def listWidget_Referrers_current_changed(self, QModelIndex_current):
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

    def listWidget_Referrers_item_double_clicked(self, item):
        self.parent().disassemble_expression(SysUtils.extract_address(item.text()), append_to_travel_history=True)

    def listWidget_Referrers_context_menu_event(self, event):
        def copy_to_clipboard(row):
            app.clipboard().setText(self.listWidget_Referrers.item(row).text())

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

    def closeEvent(self, QCloseEvent):

        instances.remove(self)


if __name__ == "__main__":
    help_message = "usage: sudo ./PINCE.py\n" \
               " --ipc=path\n\tSpecifies the shared memory path, defaults to /dev/shm, this can be used to " \
               "be able to run PINCE without super user access, it requires you to run " \
               "'echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope'" \
               "first though (see 'man ptrace' for more information)\n" \
               "-h --help\n\tDisplay this message"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["ipc=", "help"])
    except getopt.GetoptError:
        logging.error(help_message)
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_message)
            sys.exit(1)
        if opt == "--ipc":
            type_defs.IPC_PATHS.PINCE_IPC_PATH = arg

    logging.basicConfig(level=logging.DEBUG)
    print("ipc path: {}".format(type_defs.IPC_PATHS.PINCE_IPC_PATH))
    app = QApplication(sys.argv)
    window = MainForm()
    window.show()
    sys.exit(app.exec_())
