from PyQt5.QtWidgets import QDialog, QMenu, QMessageBox

from application.GUI.AddAddressManuallyDialog import Ui_Dialog as ManualAddressDialog
from application.GUI.CustomValidators.HexValidator import QHexValidator
from libPINCE import type_defs, GuiUtils, GDB_Engine

# Add Address Manually Dialog
class ManualAddressDialogForm(QDialog, ManualAddressDialog):
    def __init__(self, parent=None, description="No Description", address="0x",
                 index=type_defs.VALUE_INDEX.INDEX_4BYTES, length=10, zero_terminate=True):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.adjustSize()
        self.setMinimumWidth(300)
        self.setFixedHeight(self.height())
        self.lineEdit_length.setValidator(QHexValidator(999, self))
        GuiUtils.fill_value_combobox(self.comboBox_ValueType, index)
        self.lineEdit_description.setText(description)
        self.lineEdit_address.setText(address)
        if type_defs.VALUE_INDEX.is_string(self.comboBox_ValueType.currentIndex()):
            self.label_length.show()
            self.lineEdit_length.show()
            try:
                length = str(length)
            except:
                length = "10"
            self.lineEdit_length.setText(length)
            self.checkBox_zeroterminate.show()
            self.checkBox_zeroterminate.setChecked(zero_terminate)
        elif self.comboBox_ValueType.currentIndex() == type_defs.VALUE_INDEX.INDEX_AOB:
            self.label_length.show()
            self.lineEdit_length.show()
            try:
                length = str(length)
            except:
                length = "10"
            self.lineEdit_length.setText(length)
            self.checkBox_zeroterminate.hide()
        else:
            self.label_length.hide()
            self.lineEdit_length.hide()
            self.checkBox_zeroterminate.hide()
        self.comboBox_ValueType.currentIndexChanged.connect(self.comboBox_ValueType_current_index_changed)
        self.lineEdit_length.textChanged.connect(self.update_value_of_address)
        self.checkBox_zeroterminate.stateChanged.connect(self.update_value_of_address)
        self.lineEdit_address.textChanged.connect(self.update_value_of_address)
        self.label_valueofaddress.contextMenuEvent = self.label_valueofaddress_context_menu_event
        self.update_value_of_address()

    def label_valueofaddress_context_menu_event(self, event):
        menu = QMenu()
        refresh = menu.addAction("Refresh")
        font_size = self.label_valueofaddress.font().pointSize()
        menu.setStyleSheet("font-size: " + str(font_size) + "pt;")
        action = menu.exec_(event.globalPos())
        actions = {
            refresh: self.update_value_of_address
        }
        try:
            actions[action]()
        except KeyError:
            pass

    def update_value_of_address(self):
        address = GDB_Engine.examine_expression(self.lineEdit_address.text()).address
        if not address:
            self.label_valueofaddress.setText("<font color=red>??</font>")
            return
        address_type = self.comboBox_ValueType.currentIndex()
        if address_type == type_defs.VALUE_INDEX.INDEX_AOB:
            length = self.lineEdit_length.text()
            value = GDB_Engine.read_memory(address, address_type, length)
        elif type_defs.VALUE_INDEX.is_string(address_type):
            length = self.lineEdit_length.text()
            is_zeroterminate = self.checkBox_zeroterminate.isChecked()
            value = GDB_Engine.read_memory(address, address_type, length, is_zeroterminate)
        else:
            value = GDB_Engine.read_memory(address, address_type)
        self.label_valueofaddress.setText("<font color=red>??</font>" if value is None else str(value))

    def comboBox_ValueType_current_index_changed(self):
        if type_defs.VALUE_INDEX.is_string(self.comboBox_ValueType.currentIndex()):
            self.label_length.show()
            self.lineEdit_length.show()
            self.checkBox_zeroterminate.show()
        elif self.comboBox_ValueType.currentIndex() == type_defs.VALUE_INDEX.INDEX_AOB:
            self.label_length.show()
            self.lineEdit_length.show()
            self.checkBox_zeroterminate.hide()
        else:
            self.label_length.hide()
            self.lineEdit_length.hide()
            self.checkBox_zeroterminate.hide()
        self.update_value_of_address()

    def reject(self):
        super(ManualAddressDialogForm, self).reject()

    def accept(self):
        if self.label_length.isVisible():
            length = self.lineEdit_length.text()
            try:
                length = int(length, 0)
            except:
                QMessageBox.information(self, "Error", "Length is not valid")
                return
            if not length > 0:
                QMessageBox.information(self, "Error", "Length must be greater than 0")
                return
        super(ManualAddressDialogForm, self).accept()

    def get_values(self):
        description = self.lineEdit_description.text()
        address = self.lineEdit_address.text()
        length = self.lineEdit_length.text()
        try:
            length = int(length, 0)
        except:
            length = 0
        zero_terminate = False
        if self.checkBox_zeroterminate.isChecked():
            zero_terminate = True
        address_type = self.comboBox_ValueType.currentIndex()
        return description, address, address_type, length, zero_terminate