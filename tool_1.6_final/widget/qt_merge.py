from widget import qt_form

import tkinter
import json
import os
from PyQt5.QtWidgets import QFileDialog, QDialog
from widget.qt_form import Ui_MergeJson, Ui_MergeJsonDialog, Ui_Load

form_class = qt_form.Ui_MergeJson
form_class_2 = qt_form.Ui_MergeJsonDialog


class MergeDialog(QDialog, form_class):
    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.dir = ""  # directory
        self.name = ""  # region name

        self.json_file, self.json_files, self.json_dir, self.result = [], [], [], []
        self.json_flag = 0
        self.annotation = []
        self.json_file_name = "new_via_region_json_test!!"

        # self.control()
        self.pushButton.clicked.connect(self.help)
        self.pushButton_3.clicked.connect(self.json_file_dir)
        self.pushButton_4.clicked.connect(self.json_dirr)
        self.pushButton_5.clicked.connect(self.Merging)
        self.pushButton_6.clicked.connect(self.Merging_opt)
        self.ST_json_dir = os.getcwd()

    def Merging(self):
        # JSON Merging Execute
        if not self.annotation:
            # Merging 할 annotation이 없으면
            print("No file's in Merging List")
            return super()
        for j in range(len(self.annotation) - 1):
            self.annotation[0].update(self.annotation[j + 1])
        with open(self.json_file_name + ".json", "w") as new:
            json.dump(self.annotation[0], new, indent="\t")

        window = tkinter.Tk()  # 최상위 레벨 윈도우창 생성
        window.title("Merging Completed")
        window.geometry("350x150+800+500")
        window.resizable(1, 1)
        widget = tkinter.Label(window, text="New Json File Name : " + self.json_file_name +
                                            "\n\nAt DIR : " + os.getcwd() + "\n\nMerging Completed")
        widget.pack()

        window.mainloop()

    def Merging_opt(self):
        # Merging Option : Dir opt, Name opt
        opt_win = mergeopt()
        r = opt_win.showModal()
        if r:
            self.text = opt_win.json_directory
            self.text_2 = opt_win.json_name
            self.ST_json_dir = self.text
            self.json_file_name = self.text_2

    def json_dirr(self):
        # Find Directory opt
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        self.json_dir = (QFileDialog.getExistingDirectory(self))
        if self.json_dir == "":
            # 취소 시
            return super()
        self.json_files = os.listdir(self.json_dir)

        for s in self.json_files:
            if '.json' in s:
                self.result.append(s)
        for i in self.result:
            self.listWidget.addItem(self.json_dir + '/' + str(i))
            self.annotation.append(json.load(open(os.path.join(self.json_dir, i))))
        self.json_dir = []

    def json_file_dir(self):
        # Find json file opt
        options = QFileDialog.Options()  # directory finder 열기
        options |= QFileDialog.ShowDirsOnly
        self.json_file.append(QFileDialog.getOpenFileName(self))
        if self.json_file[self.json_flag][0] == "":
            # 취소 시
            return super()
        self.listWidget.addItem(self.json_file[self.json_flag][0])
        self.annotation.append(json.load(open(os.path.join(self.json_file[self.json_flag][0]))))
        self.json_flag += 1

    def help(self):
        window = tkinter.Tk()  # 최상위 레벨 윈도우창 생성
        window.title("Merging Completed")
        window.geometry("350x150+750+500")
        window.resizable(0, 0)
        widget = tkinter.Label(window, text="JSON File Merge Feature" + \
                                            "\n\nYou can set new JSON File's name &\n  set location of the JSON File's DIR through \'Merge_opt\'" + \
                                            "\nWhen you push merge button in this window, " + \
                                            "\n  JSON file's in \'JSON File List\' will be merged" + \
                                            "\n\'new_via_style_region\' is the initial name setting"
                                            "\nThank you")
        widget.pack()
        window.mainloop()

    def showModal(self):
        # 창을 실행시켜줌
        return super().exec_()


class mergeopt(QDialog, form_class_2):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept_button)
        self.buttonBox.rejected.connect(self.reject_button)
        self.toolButton.clicked.connect(self.json_dir)

    def accept_button(self):
        self.json_directory = self.textEdit_4.toPlainText()
        self.json_name = self.textEdit_3.toPlainText()
        self.accept()

    def reject_button(self):
        self.reject()

    def showModal(self):
        return super().exec_()

    def json_dir(self):
        options = QFileDialog.Options()  # directory finder 열기
        options |= QFileDialog.ShowDirsOnly
        self.json_direc = (QFileDialog.getExistingDirectory(self))
        self.textEdit_4.setText(self.json_direc)

