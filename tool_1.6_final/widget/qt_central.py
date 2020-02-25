from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from widget import qt_image, qt_leftside


class CentralWidget(QWidget):
    def __init__(self, mode):
        super().__init__()

        # mode
        self.mode = mode

        # key set
        self.KEY_CTRL = False

        # Image Widget 생성
        self.image_widget = qt_image.ImageWidget(self.mode, self)
        self.leftside_widget = qt_leftside.LeftSideWidget(self.mode, self)

        formbox = QHBoxLayout()
        leftmask = QVBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()

        pb = QPushButton()
        pb.setMinimumWidth(275)
        pb.setMaximumHeight(2)
        pb.setFlat(True)  # setFlat(True) : 테두리 없애기 + 해당 button Push 무효화
        leftmask.addWidget(pb)

        left.addWidget(self.leftside_widget.setupUi(self))
        left.addStretch(0)

        right.addWidget(self.image_widget.view)

        formbox.addLayout(leftmask)
        formbox.addLayout(left)
        formbox.addLayout(right)
        self.setLayout(formbox)

        self.leftside_widget.update()

    def wheelEvent(self, e):
        if self.image_widget.view.KEY_CTRL:
            value = 1 if e.angleDelta().y() > 0 else -1

            if self.mode.CURRENT == 2:
                # magic wand
                self.mode.DRAW_MASK_TOLERANCE = self.mode.DRAW_MASK_TOLERANCE + value * 2
                if value < 0 and self.mode.DRAW_MASK_TOLERANCE < self.mode.DRAW_MASK_TOLERANCE_MIN:
                    self.mode.DRAW_MASK_TOLERANCE = self.mode.DRAW_MASK_TOLERANCE_MIN
                elif self.mode.DRAW_MASK_TOLERANCE > self.mode.DRAW_MASK_TOLERANCE_MAX:
                    self.mode.DRAW_MASK_TOLERANCE = self.mode.DRAW_MASK_TOLERANCE_MAX
                self.leftside_widget.update()

            elif self.mode.CURRENT == 3:
                # paint
                self.mode.DRAW_PAINT_WIDTH = self.mode.DRAW_PAINT_WIDTH + value * 2
                if value < 0 and self.mode.DRAW_PAINT_WIDTH < self.mode.DRAW_PAINT_WIDTH_MIN:
                    self.mode.DRAW_PAINT_WIDTH = self.mode.DRAW_PAINT_WIDTH_MIN
                elif self.mode.DRAW_PAINT_WIDTH > self.mode.DRAW_PAINT_WIDTH_MAX:
                        self.mode.DRAW_PAINT_WIDTH = self.mode.DRAW_PAINT_WIDTH_MAX
                self.leftside_widget.update()

    def keyPressEvent(self, e):
        # image adjsut key
        MODE_CHANGE = -1
        if e.key() == Qt.Key_F1 or e.key() == Qt.Key_R:
            MODE_CHANGE = 0
        elif e.key() == Qt.Key_F2:
            MODE_CHANGE = 1
            print(2)
        elif e.key() == Qt.Key_F3:
            MODE_CHANGE = 2
        elif e.key() == Qt.Key_F4:
            MODE_CHANGE = 3
        elif e.key() == Qt.Key_F5:
            MODE_CHANGE = 4

        if MODE_CHANGE != -1:
            self.mode.IMAGE_ADJUST_MODE = MODE_CHANGE
            self.image_widget.redraw(backup_mask=True)
            return

        # parameter set
        if e.key() == Qt.Key_A:
            # parm1 down
            if self.mode.IMAGE_ADJUST_MODE in [2, 3]:
                # crack detector opening
                self.mode.IMAGE_ADJUST_OPENING_SIZE -= 2
                if self.mode.IMAGE_ADJUST_OPENING_SIZE < 1:
                    self.mode.IMAGE_ADJUST_OPENING_SIZE = 1

            elif self.mode.IMAGE_ADJUST_MODE == 4:
                # edge detector min value
                self.mode.IMAGE_ADJUST_CANNY_MIN -= 2
                if self.mode.IMAGE_ADJUST_CANNY_MIN < 0:
                    self.mode.IMAGE_ADJUST_CANNY_MIN = 0

            self.image_widget.redraw(backup_mask=True)

        elif e.key() == Qt.Key_S:
            # parm1 up
            if self.mode.IMAGE_ADJUST_MODE in [2, 3]:
                # crack detector opening
                self.mode.IMAGE_ADJUST_OPENING_SIZE += 2
                if self.mode.IMAGE_ADJUST_OPENING_SIZE > 51:
                    self.mode.IMAGE_ADJUST_OPENING_SIZE = 51

            elif self.mode.IMAGE_ADJUST_MODE == 4:
                # edge detector min value
                self.mode.IMAGE_ADJUST_CANNY_MIN += 2
                if self.mode.IMAGE_ADJUST_CANNY_MIN > 150:
                    self.mode.IMAGE_ADJUST_CANNY_MIN = 150

            self.image_widget.redraw(backup_mask=True)

        elif e.key() == Qt.Key_D:
            # parm2 down
            if self.mode.IMAGE_ADJUST_MODE == 3:
                # crack detector
                self.mode.IMAGE_ADJUST_CLOSING_SIZE -= 2
                if self.mode.IMAGE_ADJUST_CLOSING_SIZE < 1:
                    self.mode.IMAGE_ADJUST_CLOSING_SIZE = 1

            elif self.mode.IMAGE_ADJUST_MODE == 4:
                # edge detector min value
                self.mode.IMAGE_ADJUST_CANNY_MAX -= 5
                if self.mode.IMAGE_ADJUST_CANNY_MAX < 0:
                    self.mode.IMAGE_ADJUST_CANNY_MAX = 0

            self.image_widget.redraw(backup_mask=True)

        elif e.key() == Qt.Key_F:
            # parm2 up
            if self.mode.IMAGE_ADJUST_MODE == 3:
                # crack detector
                self.mode.IMAGE_ADJUST_CLOSING_SIZE += 2
                if self.mode.IMAGE_ADJUST_CLOSING_SIZE > 51:
                    self.mode.IMAGE_ADJUST_CLOSING_SIZE = 51

            elif self.mode.IMAGE_ADJUST_MODE == 4:
                # edge detector min value
                self.mode.IMAGE_ADJUST_CANNY_MAX += 5
                if self.mode.IMAGE_ADJUST_CANNY_MAX > 200:
                    self.mode.IMAGE_ADJUST_CANNY_MAX = 200

            self.image_widget.redraw(backup_mask=True)