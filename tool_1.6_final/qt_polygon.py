from PyQt5.QtWidgets import QGraphicsPolygonItem


class PolygonItem(QGraphicsPolygonItem):
    def __init__(self, parent, polygon, attribute, id = -1):
        super().__init__(polygon)
        self.parent = parent
        self.polygon = polygon
        self.attribute = attribute
        self.id = id

        print('polygon id')

        self.text_item = None

        self.setAcceptHoverEvents(True)

    def mouseDoubleClickEvent(self, e):
        self.parent.callback_polygon_double_click(self)

    def hoverEnterEvent(self, e):
        self.parent.callback_polygon_hover_enter(self)

    def hoverMoveEvent(self, e):
        self.parent.callback_polygon_hover_move(self)

    def hoverLeaveEvent(self, e):
        self.parent.callback_polygon_hover_leave(self)