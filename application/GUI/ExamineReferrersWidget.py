# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ExamineReferrersWidget.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1025, 530)
        Form.setToolTip("")
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setObjectName("gridLayout")
        self.splitter = QtWidgets.QSplitter(Form)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.layoutWidget = QtWidgets.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lineEdit_Regex = QtWidgets.QLineEdit(self.layoutWidget)
        self.lineEdit_Regex.setObjectName("lineEdit_Regex")
        self.horizontalLayout_2.addWidget(self.lineEdit_Regex)
        self.checkBox_CaseSensitive = QtWidgets.QCheckBox(self.layoutWidget)
        self.checkBox_CaseSensitive.setObjectName("checkBox_CaseSensitive")
        self.horizontalLayout_2.addWidget(self.checkBox_CaseSensitive)
        self.checkBox_Regex = QtWidgets.QCheckBox(self.layoutWidget)
        self.checkBox_Regex.setObjectName("checkBox_Regex")
        self.horizontalLayout_2.addWidget(self.checkBox_Regex)
        self.pushButton_Search = QtWidgets.QPushButton(self.layoutWidget)
        self.pushButton_Search.setObjectName("pushButton_Search")
        self.horizontalLayout_2.addWidget(self.pushButton_Search)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.listWidget_Referrers = QtWidgets.QListWidget(self.layoutWidget)
        self.listWidget_Referrers.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.listWidget_Referrers.setObjectName("listWidget_Referrers")
        self.verticalLayout.addWidget(self.listWidget_Referrers)
        self.textBrowser_DisasInfo = QtWidgets.QTextBrowser(self.splitter)
        self.textBrowser_DisasInfo.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textBrowser_DisasInfo.setObjectName("textBrowser_DisasInfo")
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Examine Referrers"))
        self.lineEdit_Regex.setToolTip(_translate("Form", "Enter a string or a python regex"))
        self.lineEdit_Regex.setPlaceholderText(_translate("Form", "Enter a string or a python regex"))
        self.checkBox_CaseSensitive.setToolTip(_translate("Form", "Ignore case if checked"))
        self.checkBox_CaseSensitive.setText(_translate("Form", "Case sensitive"))
        self.checkBox_Regex.setToolTip(_translate("Form", "Your string will be treated as a regex if checked"))
        self.checkBox_Regex.setText(_translate("Form", "Regex"))
        self.pushButton_Search.setText(_translate("Form", "Search(Enter)"))

