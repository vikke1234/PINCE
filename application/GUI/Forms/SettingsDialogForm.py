import os
import re

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QKeySequenceEdit, QMessageBox, QFileDialog

from application import Hotkeys
from application.GUI.Forms.InputDialogForm import InputDialogForm
from application.GUI.SettingsDialog import Ui_Dialog as SettingsDialog
from libPINCE import GuiUtils, type_defs, GDB_Engine, SysUtils


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