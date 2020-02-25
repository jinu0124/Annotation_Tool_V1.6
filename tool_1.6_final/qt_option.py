from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtGui import QColor


class EditMode:
    _MODE_COUNT = 4

    def __init__(self):
        self.set_default()

    def set_default(self):
        # Default Mode
        self.set_mode(0)

        # Edit Setting
        self.DRAW_PEN_COLOR = QColor(0, 0, 0)
        self.DRAW_PEN_COLOR_WARNNING = QColor(255, 0, 0)
        self.DRAW_PEN_COLOR_SELECT = QColor(0, 255, 255)
        self.DRAW_PEN_WIDTH = 3
        self.DRAW_PEN_WIDTH_SELECT = 6
        self.DRAW_BRUSH_COLOR = QColor(0, 0, 255, 80)

        self.DRAW_MASK_COLOR = QColor(255, 255, 0, 100)
        self.DRAW_MASK_TOLERANCE = 10
        self.DRAW_MASK_TOLERANCE_MIN = 1
        self.DRAW_MASK_TOLERANCE_MAX = 100

        self.DRAW_PAINT_WIDTH = 30
        self.DRAW_PAINT_WIDTH_MIN = 1
        self.DRAW_PAINT_WIDTH_MAX = 100
        self.DRAW_PAINT_MODE = True

        self.POLYGON_CURRENT_ATTRIBUTE = {"name" : "none"}
        self.POLYGON_BRUSH_COLOR = {}

        self.IMAGE_ADJUST_MODE = 0
        self.IMAGE_ADJUST_OPENING_SIZE = 3
        self.IMAGE_ADJUST_CLOSING_SIZE = 7
        self.IMAGE_ADJUST_CANNY_MIN = 50
        self.IMAGE_ADJUST_CANNY_MAX = 100

        # System Setting
        self.POLYGON_END_THRESHOLD = 50

        # Window Setting
        self.SCROLLBAR_VIEW = True

    def set_mode(self, mode):
        assert mode < self._MODE_COUNT, "Invalid edit mode"
        self.CURRENT = mode
        self.VIEW_DRAG_MODE = QGraphicsView.NoDrag

        if mode == 0:
            # 1. Normal Mode : panning view and select object
            self.VIEW_DRAG_MODE = QGraphicsView.ScrollHandDrag
            pass

        elif mode == 1:
            # 2. Draw Mode : draw polygon
            pass