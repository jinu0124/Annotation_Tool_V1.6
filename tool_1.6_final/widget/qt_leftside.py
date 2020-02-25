import os

from PyQt5.QtWidgets import QWidget, QColorDialog
from PyQt5.QtGui import QColor
from widget import qt_form

class LeftSideWidget(QWidget, qt_form.Ui_LeftForm):
    def __init__(self, mode, parent):
        super().__init__()
        self.mode = mode
        self.parent = parent

        # Attribute Config 선언 & click event
        self.top = 0
        self.attr_dict = dict()

        self.add_color = ""

    def load_filelist(self, dataset):
        for i in dataset.image_dirs:
            self.listWidget.addItem(str(os.path.basename(i)))

    def select_image(self, image_widget):
        # When image is Double Clicked Event -> Direct Move to applicable image
        image_file = self.listWidget.currentItem().text()
        image_count = self.listWidget.count()
        for i in range(image_count):
            if image_file == self.listWidget.item(i).text():
                image_widget.select_image(i)
                break

    def select_image_list(self, image_id):
        if not image_id < self.listWidget.count():
            return
        self.listWidget.setCurrentRow(image_id)

    def color_select(self):
        # color select
        color = QColorDialog.getColor()

        if color.isValid():
            self.listWidget_3.clear()
            self.listWidget_3.addItem(color.name())
            self.add_color = str(color.name())

    def select_attr_list(self):
        # When DoubleClickedEvent -> Attribute name & color apply
        attr = self.listWidget_2.currentItem().text()
        attr_index = self.listWidget_2.count()
        for i in range(attr_index):
            if str(self.attr_dict[i]) == attr:
                self.mode.POLYGON_CURRENT_ATTRIBUTE['name'] = str(self.attr_dict[i]['name'])

    def del_attr_list(self):
        # Attribute List의 attribute 삭제 / listWidget & dict에 동기적으로 삭제
        attr = self.listWidget_2.currentItem()
        flag = 0

        for index in range(self.listWidget_2.count()):  # 객체 반환
            if attr == self.listWidget_2.item(index):
                self.listWidget_2.takeItem(flag).text()
                del self.mode.POLYGON_BRUSH_COLOR[str(self.attr_dict[flag]['name'])]
                del self.attr_dict[flag]
                if flag != len(self.attr_dict):
                    for i in range(len(self.attr_dict) - flag):
                        self.attr_dict[flag + i] = self.attr_dict[flag + i + 1]
                    del self.attr_dict[len(self.attr_dict) - 1]
                self.top -= 1
                break
            flag += 1
        self.parent.image_widget.redraw()

    def add_attr_list(self):
        # Attribute List에 Attribute 추가 / listWidget & dict에 동기적으로 추가
        name_dupl = []
        name = self.lineEdit.text()

        for i in range(self.listWidget_2.count()):
            name_dupl.append(self.listWidget_2.item(i).text())
            if name in name_dupl[i]:
                return super()

        if self.add_color is not "":
            self.attr_dict[self.top] = {'name': name, 'color': self.add_color}
            self.listWidget_2.addItem(str(self.attr_dict[self.top]))

            # select
            self.listWidget_2.setCurrentRow(self.top)
            self.select_attr_list()

            # redraw
            color = QColor(self.attr_dict[self.top]['color'])
            color.setAlpha(80)
            self.mode.POLYGON_BRUSH_COLOR[str(self.attr_dict[self.top]['name'])] = color
            self.parent.image_widget.redraw()

            self.top += 1

    def fast_color(self, color):
        # RGB
        self.listWidget_3.clear()
        self.listWidget_3.addItem(str(color))
        self.add_color = color

    def tolerance_input(self):
        value = int(self.lineEdit_2.text())
        self.mode.DRAW_MASK_TOLERANCE = self.tolerance = value
        self.horizontalSlider.setValue(value)

    def tolerance_ctrl(self):
        # 0 ~ 100
        self.mode.DRAW_MASK_TOLERANCE = self.tolerance = int(self.horizontalSlider.value())
        self.lineEdit_2.setText(str(self.tolerance))

    def paint_input(self):
        value = int(self.lineEdit_3.text())
        self.mode.DRAW_PAINT_WIDTH = self.paint = value
        self.horizontalSlider_2.setValue(value)

    def paint_ctrl(self):
        # 0 ~ 100
        self.mode.DRAW_PAINT_WIDTH = self.paint = int(self.horizontalSlider_2.value())
        self.lineEdit_3.setText(str(self.paint))

    def update(self):
        self.tolerance = self.mode.DRAW_MASK_TOLERANCE
        self.horizontalSlider.setValue(self.tolerance)
        self.lineEdit_2.setText(str(self.tolerance))

        self.paint = self.mode.DRAW_PAINT_WIDTH
        self.horizontalSlider_2.setValue(self.paint)
        self.lineEdit_3.setText(str(self.paint))