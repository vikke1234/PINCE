#  Copyright (c) 2020 Viktor Horsmanheimo <viktor.horsmanheimo@gmail.com>
#  Copyright (C) 2016-2017 Korcan Karaokçu <korcankaraokcu@gmail.com>
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

from PyQt5.QtCore import QThread, pyqtSignal

from libPINCE import GDB_Engine, type_defs


class CheckInferiorStatus(QThread):
    process_stopped = pyqtSignal()
    process_running = pyqtSignal()

    def run(self):
        while True:
            with GDB_Engine.status_changed_condition:
                GDB_Engine.status_changed_condition.wait()
            if GDB_Engine.inferior_status == type_defs.INFERIOR_STATUS.INFERIOR_STOPPED and GDB_Engine.temporary_execution_bool != True:
                print("execute condition: "+ str(GDB_Engine.temporary_execution_bool))
                self.process_stopped.emit()
            elif GDB_Engine.inferior_status == type_defs.INFERIOR_STATUS.INFERIOR_RUNNING and GDB_Engine.temporary_execution_bool != True:
                self.process_running.emit()