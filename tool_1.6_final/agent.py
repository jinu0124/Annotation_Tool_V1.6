from PyQt5.QtWidgets import QApplication
import sys
import qt_main

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = qt_main.ToolWindow()
    sys.exit(app.exec_())