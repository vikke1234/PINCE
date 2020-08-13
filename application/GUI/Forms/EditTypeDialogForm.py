from PyQt5.QtWidgets import QDialog, QMessageBox

from application.GUI.CustomValidators.HexValidator import QHexValidator
from application.GUI.EditTypeDialog import Ui_Dialog as EditTypeDialog
from libPINCE import type_defs, GuiUtils


class EditTypeDialogForm(QDialog, EditTypeDialog):
    def __init__(self, parent=None, index=type_defs.VALUE_INDEX.INDEX_4BYTES, length=10, zero_terminate=True):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setMaximumSize(100, 100)
        self.lineEdit_Length.setValidator(QHexValidator(999, self))
        GuiUtils.fill_value_combobox(self.comboBox_ValueType, index)

        is_str = type_defs.VALUE_INDEX.is_string(self.comboBox_ValueType.currentIndex())
        str_or_aob = is_str or self.comboBox_ValueType.currentIndex() == type_defs.VALUE_INDEX.INDEX_AOB
        self.label_Length.setVisible(str_or_aob)
        self.lineEdit_Length.setVisible(str_or_aob)
        self.checkBox_ZeroTerminate.setVisible(is_str)
        self.checkBox_ZeroTerminate.setChecked(zero_terminate)
        try:
            length = str(length)
        except ValueError:
            length = "10"
        self.lineEdit_Length.setText(length)
        self.comboBox_ValueType.currentIndexChanged.connect(self.comboBox_ValueType_current_index_changed)

    def comboBox_ValueType_current_index_changed(self):
        aob_or_str = type_defs.VALUE_INDEX.is_string(self.comboBox_ValueType.currentIndex()) or \
                     (self.comboBox_ValueType.currentIndex() == type_defs.VALUE_INDEX.INDEX_AOB)
        self.label_Length.setVisible(aob_or_str)
        self.lineEdit_Length.setVisible(aob_or_str)
        self.checkBox_ZeroTerminate.setVisible(type_defs.VALUE_INDEX.is_string(self.comboBox_ValueType.currentIndex()))

    def reject(self):
        super(EditTypeDialogForm, self).reject()

    def accept(self):
        if self.label_Length.isVisible():
            length = self.lineEdit_Length.text()
            try:
                length = int(length, 0)
            except ValueError:
                QMessageBox.information(self, "Error", "Length is not valid")
                return
            if not length > 0:
                QMessageBox.information(self, "Error", "Length must be greater than 0")
                return
        super(EditTypeDialogForm, self).accept()

    def get_values(self):
        length = self.lineEdit_Length.text()
        try:
            length = int(length, 0)
        except ValueError:
            length = 0
        zero_terminate = False
        if self.checkBox_ZeroTerminate.isChecked():
            zero_terminate = True
        address_type = self.comboBox_ValueType.currentIndex()
        return address_type, length, zero_terminate
