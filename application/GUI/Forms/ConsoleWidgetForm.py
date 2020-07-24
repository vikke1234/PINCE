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
from PyQt5.QtCore import QStringListModel, Qt
from PyQt5.QtGui import QKeySequence, QTextCursor
from PyQt5.QtWidgets import QWidget, QCompleter, QShortcut

from application.GUI.Forms.TextEditDialogForm import TextEditDialogForm
from application.GUI.ConsoleWidget import Ui_Form as ConsoleWidget
from application.Threads.AwaitAsyncOutputThread import AwaitAsyncOutput
from application.instance_storage import instances
from libPINCE import GuiUtils, GDB_Engine, type_defs


class ConsoleWidgetForm(QWidget, ConsoleWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        instances.append(self)
        GuiUtils.center(self)
        self.completion_model = QStringListModel()
        self.completer = QCompleter()
        self.completer.setModel(self.completion_model)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setMaxVisibleItems(8)
        self.lineEdit.setCompleter(self.completer)
        self.quit_commands = ("q", "quit", "-gdb-exit")
        self.input_history = [""]
        self.current_history_index = -1
        self.await_async_output_thread = AwaitAsyncOutput()
        self.await_async_output_thread.async_output_ready.connect(self.on_async_output)
        self.await_async_output_thread.start()
        self.pushButton_Send.clicked.connect(self.communicate)
        self.pushButton_SendCtrl.clicked.connect(lambda: self.communicate(control=True))
        self.shortcut_send = QShortcut(QKeySequence("Return"), self)
        self.shortcut_send.activated.connect(self.communicate)
        self.shortcut_complete_command = QShortcut(QKeySequence("Tab"), self)
        self.shortcut_complete_command.activated.connect(self.complete_command)
        self.shortcut_send_ctrl = QShortcut(QKeySequence("Ctrl+C"), self)
        self.shortcut_send_ctrl.activated.connect(lambda: self.communicate(control=True))
        self.shortcut_multiline_mode = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.shortcut_multiline_mode.activated.connect(self.enter_multiline_mode)
        self.lineEdit.textEdited.connect(self.finish_completion)

        # Saving the original function because super() doesn't work when we override functions like this
        self.lineEdit.keyPressEvent_original = self.lineEdit.keyPressEvent
        self.lineEdit.keyPressEvent = self.lineEdit_key_press_event
        self.reset_console_text()

    def communicate(self, control=False):
        self.current_history_index = -1
        self.input_history[-1] = ""
        if control:
            console_input = "/Ctrl+C"
        else:
            console_input = self.lineEdit.text()
            last_input = self.input_history[-2] if len(self.input_history) > 1 else ""
            if console_input != last_input and console_input != "":
                self.input_history[-1] = console_input
                self.input_history.append("")
        if console_input.lower() == "/clear":
            self.lineEdit.clear()
            self.reset_console_text()
            return
        self.lineEdit.clear()
        if console_input.strip().lower() in self.quit_commands:
            console_output = "Quitting current session will crash PINCE"
        else:
            if not control:
                if self.radioButton_CLI.isChecked():
                    console_output = GDB_Engine.send_command(console_input, cli_output=True)
                else:
                    console_output = GDB_Engine.send_command(console_input)
                if not console_output:
                    if GDB_Engine.inferior_status == type_defs.INFERIOR_STATUS.INFERIOR_RUNNING:
                        console_output = "Inferior is running"
            else:
                GDB_Engine.interrupt_inferior()
                console_output = ""
        self.textBrowser.append("-->" + console_input)
        if console_output:
            self.textBrowser.append(console_output)
        self.scroll_to_bottom()

    def reset_console_text(self):
        self.textBrowser.clear()
        self.textBrowser.append("Hotkeys:")
        self.textBrowser.append("----------------------------")
        self.textBrowser.append("Send=Enter                 |")
        self.textBrowser.append("Send ctrl+c=Ctrl+C         |")
        self.textBrowser.append("Multi-line mode=Ctrl+Enter |")
        self.textBrowser.append("Complete command=Tab       |")
        self.textBrowser.append("----------------------------")
        self.textBrowser.append("Commands:")
        self.textBrowser.append("----------------------------------------------------------")
        self.textBrowser.append("/clear: Clear the console                                |")
        self.textBrowser.append("phase-out: Detach from the current process               |")
        self.textBrowser.append("phase-in: Attach back to the previously detached process |")
        self.textBrowser.append(
            "---------------------------------------------------------------------------------------------------")
        self.textBrowser.append(
            "pince-init-so-file so_file_path: Initializes 'lib' variable                                       |")
        self.textBrowser.append(
            "pince-get-so-file-information: Get information about current lib                                  |")
        self.textBrowser.append(
            "pince-execute-from-so-file lib.func(params): Execute a function from lib                          |")
        self.textBrowser.append(
            "# Check https://github.com/korcankaraokcu/PINCE/wiki#extending-pince-with-so-files for an example |")
        self.textBrowser.append(
            "# CLI output mode doesn't work very well with .so extensions, use MI output mode instead          |")
        self.textBrowser.append(
            "---------------------------------------------------------------------------------------------------")
        self.textBrowser.append("You can change the output mode from bottom right")
        self.textBrowser.append("Note: Changing output mode only affects commands sent. Any other " +
                                "output coming from external sources(e.g async output) will be shown in MI format")

    def scroll_to_bottom(self):
        cursor = self.textBrowser.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.textBrowser.setTextCursor(cursor)
        self.textBrowser.ensureCursorVisible()

    def enter_multiline_mode(self):
        multiline_dialog = TextEditDialogForm(text=self.lineEdit.text())
        if multiline_dialog.exec_():
            self.lineEdit.setText(multiline_dialog.get_values())
            self.communicate()

    def on_async_output(self, async_output):
        self.textBrowser.append(async_output)
        self.scroll_to_bottom()

    def scroll_backwards_history(self):
        try:
            new_text = self.input_history[self.current_history_index - 1]
        except IndexError:
            return
        self.input_history[self.current_history_index] = self.lineEdit.text()
        self.current_history_index -= 1
        self.lineEdit.setText(new_text)

    def scroll_forwards_history(self):
        if self.current_history_index == -1:
            return
        self.input_history[self.current_history_index] = self.lineEdit.text()
        self.current_history_index += 1
        self.lineEdit.setText(self.input_history[self.current_history_index])

    def lineEdit_key_press_event(self, event):
        actions = type_defs.KeyboardModifiersTupleDict([
            ((Qt.NoModifier, Qt.Key_Up), self.scroll_backwards_history),
            ((Qt.NoModifier, Qt.Key_Down), self.scroll_forwards_history)
        ])
        try:
            actions[event.modifiers(), event.key()]()
        except KeyError:
            self.lineEdit.keyPressEvent_original(event)

    def finish_completion(self):
        self.completion_model.setStringList([])

    def complete_command(self):
        if GDB_Engine.gdb_initialized and GDB_Engine.currentpid != -1 and self.lineEdit.text() and \
                GDB_Engine.inferior_status == type_defs.INFERIOR_STATUS.INFERIOR_STOPPED:
            self.completion_model.setStringList(GDB_Engine.complete_command(self.lineEdit.text()))
            self.completer.complete()
        else:
            self.finish_completion()

    def closeEvent(self, QCloseEvent):
        self.await_async_output_thread.stop()
        instances.remove(self)
