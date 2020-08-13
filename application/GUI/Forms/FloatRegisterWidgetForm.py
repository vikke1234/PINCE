from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTabWidget, QTableWidgetItem

from application.GUI.FloatRegisterWidget import Ui_TabWidget as FloatRegisterWidget
from application.GUI.Forms.InputDialogForm import InputDialogForm
from application.Settings import FLOAT_REGISTERS_NAME_COL, FLOAT_REGISTERS_VALUE_COL
from libPINCE import GDB_Engine, type_defs


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