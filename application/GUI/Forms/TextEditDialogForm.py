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
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QDialog, QShortcut

from application.GUI.TextEditDialog import Ui_Dialog as TextEditDialog


class TextEditDialogForm(QDialog, TextEditDialog):
    def __init__(self, parent=None, text=""):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.textEdit.setPlainText(str(text))
        self.accept_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.accept_shortcut.activated.connect(self.accept)

    def get_values(self):
        return self.textEdit.toPlainText()

    def keyPressEvent(self, key_event):
        if key_event.key() == Qt.Key_Enter:
            pass
        else:
            super(TextEditDialogForm, self).keyPressEvent(key_event)

    def accept(self):
        super(TextEditDialogForm, self).accept()
