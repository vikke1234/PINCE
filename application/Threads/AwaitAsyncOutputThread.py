#
#  Copyright (c) 2020 Viktor Horsmanheimo <viktor.horsmanheimo@gmail.com>
#  Copyright (C) 2016-2017 Korcan Karaokçu <korcankaraokcu@gmail.com>

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
import queue

from PyQt5.QtCore import QThread, pyqtSignal

from libPINCE import GDB_Engine


# Await async output from gdb
class AwaitAsyncOutput(QThread):
    async_output_ready = pyqtSignal(str)

    def __init__(self):
        super(AwaitAsyncOutput, self).__init__()
        self.queue_active = True

    def run(self):
        async_output_queue = GDB_Engine.gdb_async_output.register_queue()
        while self.queue_active:
            try:
                async_output = async_output_queue.get(timeout=5)
            except queue.Empty:
                pass
            else:
                self.async_output_ready.emit(async_output)
        GDB_Engine.gdb_async_output.delete_queue(async_output_queue)

    def stop(self):
        self.queue_active = False