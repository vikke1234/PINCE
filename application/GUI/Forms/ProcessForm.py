import psutil
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QKeyEvent, QCursor
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QFileDialog

from application.GUI.Forms.InputDialogForm import InputDialogForm
from application.GUI.SelectProcess import Ui_MainWindow as ProcessWindow
from libPINCE import GuiUtils, SysUtils

# process select window
class ProcessForm(QMainWindow, ProcessWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        GuiUtils.center_to_parent(self)
        self.refresh_process_table(self.tableWidget_ProcessTable, SysUtils.iterate_processes())
        self.pushButton_Close.clicked.connect(self.close)
        self.pushButton_Open.clicked.connect(self.pushButton_Open_clicked)
        self.pushButton_CreateProcess.clicked.connect(self.pushButton_CreateProcess_clicked)
        self.lineEdit_SearchProcess.textChanged.connect(self.generate_new_list)
        self.tableWidget_ProcessTable.itemDoubleClicked.connect(self.pushButton_Open_clicked)
        print("initialized the form")

    # refreshes process list
    def generate_new_list(self):
        text = self.lineEdit_SearchProcess.text()
        processlist = SysUtils.search_in_processes_by_name(text)
        self.refresh_process_table(self.tableWidget_ProcessTable, processlist)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            # closes the window whenever ESC key is pressed
            self.close()
        elif e.key() == Qt.Key_Return:
            self.pushButton_Open_clicked()
        elif e.key() == Qt.Key_F1:
            self.pushButton_CreateProcess_clicked()
        elif e.key() == Qt.Key_Down or e.key() == Qt.Key_Up:
            self.tableWidget_ProcessTable.keyPressEvent(QKeyEvent(QEvent.KeyPress, e.key(), Qt.NoModifier))

    # lists currently working processes to table
    def refresh_process_table(self, tablewidget, processlist):
        tablewidget.setRowCount(0)
        for process in processlist:
            pid = str(process.pid)
            try:
                username = process.username()
                name = process.name()
            except psutil.NoSuchProcess:
                continue
            current_row = tablewidget.rowCount()
            tablewidget.insertRow(current_row)
            tablewidget.setItem(current_row, 0, QTableWidgetItem(pid))
            tablewidget.setItem(current_row, 1, QTableWidgetItem(username))
            tablewidget.setItem(current_row, 2, QTableWidgetItem(name))

    # gets the pid out of the selection to attach
    def pushButton_Open_clicked(self):
        current_item = self.tableWidget_ProcessTable.item(self.tableWidget_ProcessTable.currentIndex().row(), 0)
        if current_item is None:
            QMessageBox.information(self, "Error", "Please select a process first")
        else:
            pid = int(current_item.text())
            self.setCursor(QCursor(Qt.WaitCursor))
            if self.parent().attach_to_pid(pid):
                self.close()
            self.setCursor(QCursor(Qt.ArrowCursor))

    def pushButton_CreateProcess_clicked(self):
        file_path = QFileDialog.getOpenFileName(self, "Select the target binary")[0]
        if file_path:
            items = [("Enter the optional arguments", ""), ("LD_PRELOAD .so path (optional)", "")]
            arg_dialog = InputDialogForm(item_list=items)
            if arg_dialog.exec_():
                args, ld_preload_path = arg_dialog.get_values()
            else:
                return
            self.setCursor(QCursor(Qt.WaitCursor))
            if self.parent().create_new_process(file_path, args, ld_preload_path):
                self.close()
            self.setCursor(QCursor(Qt.ArrowCursor))