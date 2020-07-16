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


from typing import List

from PyQt5 import QtCore


class Hotkey:
    """
    Hotkeys enum currently broken in the way that they can't be changed
    """
    __instances = []
    def __init__(self, name: str = "", desc: str = "",
                 default: str = "", current_value: str = "", context=QtCore.Qt.ApplicationShortcut):
        self.name = name
        self.desc = desc
        self.default = default
        self.current_value = current_value
        self.context = context
        self.__instances.append(self)

    @classmethod
    def get_hotkeys(cls) -> List:
        return cls.__instances


pause_hotkey = Hotkey("pause_hotkey", "Pause the process", "F1")
break_hotkey = Hotkey("break_hotkey", "Break the process", "F2")
continue_hotkey = Hotkey("continue_hotkey", "Continue the process", "F3")
toggle_attach_hotkey = Hotkey("toggle_attach_hotkey", "Toggle attach/detach", "Shift+F10")
