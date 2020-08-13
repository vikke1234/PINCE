from PyQt5.QtCore import Qt, QEvent, QByteArray, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QMovie
from PyQt5.QtWidgets import QDialog

from application.GUI.LoadingDialog import Ui_Dialog as LoadingDialog
from libPINCE import GuiUtils, SysUtils, GDB_Engine


class LoadingDialogForm(QDialog, LoadingDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        if parent:
            GuiUtils.center_to_parent(self)
        self.keyPressEvent = QEvent.ignore

        # Make use of this background_thread when you spawn a LoadingDialogForm
        # Warning: overrided_func() can only return one value, so if your overridden function returns more than one
        # value, refactor your overriden function to return only one object(convert tuple to list etc.)
        # Check refresh_table method of FunctionsInfoWidgetForm for exemplary usage
        self.background_thread = self.BackgroundThread()
        self.background_thread.output_ready.connect(self.accept)
        self.pushButton_Cancel.clicked.connect(self.cancel_thread)
        media_directory = SysUtils.get_media_directory()
        self.movie = QMovie(media_directory + "/LoadingDialog/ajax-loader.gif", QByteArray())
        self.label_Animated.setMovie(self.movie)
        self.movie.setScaledSize(QSize(25, 25))
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(100)
        self.movie.start()

    # This function only cancels the last command sent
    # Override this if you want to do dangerous stuff like, God forbid, background_thread.terminate()
    def cancel_thread(self):
        GDB_Engine.cancel_last_command()

    def exec_(self):
        self.background_thread.start()
        super(LoadingDialogForm, self).exec_()

    class BackgroundThread(QThread):
        output_ready = pyqtSignal(object)

        def __init__(self):
            super().__init__()

        def run(self):
            output = self.overrided_func()
            self.output_ready.emit(output)

        def overrided_func(self):
            print("Override this function")
            return 0