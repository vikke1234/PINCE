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
from PyQt5.QtWidgets import QTabWidget

from application.GUI.AboutWidget import Ui_TabWidget as AboutWidget
from libPINCE import GuiUtils


class AboutWidgetForm(QTabWidget, AboutWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        GuiUtils.center(self)
        with open("COPYING", "r") as copy_f, open("AUTHORS") as authors_f, open("THANKS") as thanks_f:
            license_text = copy_f.read()
            authors_text = authors_f.read()
            thanks_text = thanks_f.read()
            self.textBrowser_License.setPlainText(license_text)
            self.textBrowser_Contributors.append(
                "This is only a placeholder, this section may look different when the project finishes" +
                "\nIn fact, something like a demo-scene for here would look absolutely fabulous <:")
            self.textBrowser_Contributors.append("\n########")
            self.textBrowser_Contributors.append("#AUTHORS#")
            self.textBrowser_Contributors.append("########\n")
            self.textBrowser_Contributors.append(authors_text)
            self.textBrowser_Contributors.append("\n#######")
            self.textBrowser_Contributors.append("#THANKS#")
            self.textBrowser_Contributors.append("#######\n")
            self.textBrowser_Contributors.append(thanks_text)