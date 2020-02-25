from qt_polygon import PolygonItem
from qt_opencv import OpenCVImage

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem
from PyQt5.QtGui import QPixmap, QBrush, QPen, QPolygonF, QColor, QFont
from PyQt5.QtCore import Qt, QLineF, QPointF

class ImageWidget(QWidget):
    def __init__(self, mode, parent):
        super().__init__()
        self.mode = mode
        self.parent = parent
        self.dataset = None
        self.image = None
        self.view = None
        self.pixmap = None
        self.image_count = 0
        self.current = 0 # current image id

        # 새로운 graphics scene/view 생성
        self.view = ImageView(mode)

        # widget 배치
        vbox = QVBoxLayout()
        vbox.addWidget(self.view)
        self.setLayout(vbox)

        # update
        self._update()

    def load_data(self, dataset):
        self.image_count = dataset.image_count

        if self.image_count > 0:
            self.dataset = dataset
            self.current = 0
            self._image_select(self.current)
        else:
            self.dataset = None
            print("No image to import")

    def select_image(self, index):
        self.current = index if index < self.image_count else 0
        if self.dataset is not None:
            self._image_select(self.current)

    def next_image(self):
        self.current = self.current + 1 if self.current < self.image_count - 1 else 0
        if self.dataset is not None:
            self._image_select(self.current)

    def prev_image(self):
        self.current = self.current - 1 if self.current > 0 else self.image_count - 1
        if self.dataset is not None:
            self._image_select(self.current)

    def redraw(self, backup_mask=False):
        print(backup_mask)
        if self.view.image is None:
            return

        # backup
        if backup_mask:
            mask = self.view.image.backup_mask()

        # reset
        self.view.reset()

        # select / draw
        self._image_select(self.current)

        # restore
        if backup_mask:
            self.view.image.restore_mask(mask)

        # refresh
        self.view.refresh()

    def _update(self):
        if self.dataset is None:
            return

        # image adjust
        self._image_adjust(self.image)

        # view 에 image 추가
        self.view.load_image(self.image, self.metadata)

    def _image_select(self, image_id):
        image, self.metadata = self.dataset.load_image(image_id)
        self.parent.leftside_widget.select_image_list(image_id)
        self.image = OpenCVImage(image)
        self._update()

    def _image_adjust(self, image):
        assert image is not None, "Image is None"
        image.reset_image()
        if self.mode.IMAGE_ADJUST_MODE == 0:
            # restore image
            pass

        elif self.mode.IMAGE_ADJUST_MODE == 1:
            # grayscale + equalizeHist
            image.grayscale()

        elif self.mode.IMAGE_ADJUST_MODE == 2:
            # crack detector half
            image.crack_detector_opening(self.mode.IMAGE_ADJUST_OPENING_SIZE)

        elif self.mode.IMAGE_ADJUST_MODE == 3:
            # crack detector
            image.crack_detector(self.mode.IMAGE_ADJUST_OPENING_SIZE,
                                         self.mode.IMAGE_ADJUST_CLOSING_SIZE)

        elif self.mode.IMAGE_ADJUST_MODE == 4:
            # edge detector
            image.edge_detector(self.mode.IMAGE_ADJUST_CANNY_MIN,
                                        self.mode.IMAGE_ADJUST_CANNY_MAX)

class ImageView(QGraphicsView):
    def __init__(self, mode):
        # parameter
        self.mode = mode

        # create scene
        self.scene = QGraphicsScene()
        super().__init__(self.scene)
        self.setScene(self.scene)

        # use in draw sequence
        # - items : Scene 에 추가된 item list
        # - 임시 item 들은 obj에 관리된다.
        self.items = []
        self.obj = {} # View 출력을 위한 임시 저장장소
        self._object_reset()

        self.rect_p0 = None
        self.rect_p1 = None
        self.select = []

        # use in data load
        self.image = None
        self.pixmap = None
        self.image_item = None
        self.metadata = None

        # use in key event
        self._zoom = 0
        self.KEY_SHIFT = False
        self.KEY_ALT = False
        self.KEY_CTRL = False
        self.KEY_MOUSE_LEFT = False

        # backup
        self.last_mask = None
        self.last_polygon = None

        # QGraphicsView setting
        self.setDragMode(self.mode.VIEW_DRAG_MODE)
        self.setMouseTracking(True)

        # remove scrollbar option
        if not self.mode.SCROLLBAR_VIEW:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def load_image(self, image, metadata):
        self.reset()
        self.image = image

        # Qimage 를 가져온다.
        image = self.image.get_image()

        # pixmap data 생성
        pixmap = QPixmap(image)

        self.pixmap = pixmap
        self.image_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.image_item)

        self._load_metadata(metadata)

    def refresh(self):
        """ 현재 작업중인 임시 정보를 모두 삭제하고, 현재 설정값을 재설정한다.

        """
        # Object 초기화
        self._object_reset()

        # Mode 설정
        self.setDragMode(self.mode.VIEW_DRAG_MODE)

        # Data Reset
        self.rect_p0 = None
        self.rect_p1 = None
        self.select.clear()

        # Key 초기화
        self.KEY_SHIFT = False
        self.KEY_ALT = False
        self.KEY_MOUSE_LEFT = False

        # Mask Draw
        self._mask_draw()

        # update
        self._update()

    def reset(self):
        """ 이미지 정보를 포함하여 모든 정보를 삭제한다.

        """
        # Scene 에 표시되는 물체들을 제거한다.
        self._delete_items(self.items)
        self.scene.removeItem(self.image_item)

        # backup 초기화
        self.last_mask = None
        self.last_polygon = None

        # image 정보 초기화
        self.image = None
        self.pixmap = None
        self.image_item = None
        self.metadata = None

        # refresh
        self.refresh()

    def restore(self):
        print('restore')
        if self.last_mask is not None and self.image is not None:
            self.image.restore_mask(self.last_mask)
            if self.last_polygon is not None:
                self._polygon_delete(self.last_polygon)
            print('1')

            self.last_mask = None
            self.last_polygon = None
            self._mask_draw()

    def callback_selected(self, e, item):
        """ Image Item 객체가 선택되었을 때, View 에 직접 호출 할 수 있는 함수

            Image Item 객체의 event 함수에서 호출된다.
        """
        pass

    def callback_polygon_double_click(self, polygon_item):
        if self.KEY_CTRL and self.mode.CURRENT == 0:
            # delete polygon
            # 1. remove text item
            if polygon_item.text_item is not None:
                self.items.remove(polygon_item.text_item)
                self.scene.removeItem(polygon_item.text_item)

            # 2. remove polygon
            self.items.remove(polygon_item)
            self.scene.removeItem(polygon_item)
        elif self.KEY_CTRL:
            print('2')
            self._polygon_delete(polygon_item)

    def callback_polygon_hover_enter(self, polygon_item):
        if self.mode.CURRENT == 0:
            self.setDragMode(QGraphicsView.NoDrag)

    def callback_polygon_hover_move(self, polygon_item):
        if self.mode.CURRENT == 0:
            self.setDragMode(QGraphicsView.NoDrag)

    def callback_polygon_hover_leave(self, polygon_item):
        if self.mode.CURRENT == 0:
            self.setDragMode(self.mode.VIEW_DRAG_MODE)

    def _load_metadata(self, metadata):
        """ Image Annotation 을 읽어와 View 에 출력한다.


     """
        self.metadata = metadata
        polygons = metadata.out_polygons_to_list()
        for polygon in polygons:
            [attribute, x, y, id] = polygon
            assert len(x) == len(y), "Invalid polygon information in metadata"
            qpol = QPolygonF()
            for idx in range(len(x)):
                qpol.append(QPointF(x[idx], y[idx]))

            self._polygon_draw(qpol, attribute, id)

    def _update(self):
        pass

    def _delete_items(self, items):
        for item in items:
            self.scene.removeItem(item)
        items.clear()

    def _object_reset(self):
        """ Object 를 초기화한다.

            obj Dictionary 에는 view 그리기에 필요한 임시값들이 저장되어있다.
        """
        # polygon : 현재 작성중인 polygon 좌표들을 QPointF list 형태로 가지고 있는다.
        if 'polygon' not in self.obj:
            self.obj['polygon'] = []
        else:
            self.obj['polygon'].clear()

        # lines : View 에 출력되는 직선들이다.
        if 'lines' not in self.obj:
            self.obj['lines'] = []
        else:
            self._delete_items(self.obj['lines'])
            self.obj['lines'].clear()

        # mask : magicwand mask
        if 'mask' in self.obj and self.obj['mask'] is not None:
            self.scene.removeItem(self.obj['mask'])
        self.obj['mask'] = None

        # paint sign
        if 'paint' in self.obj and self.obj['paint'] is not None:
            self.scene.removeItem(self.obj['paint'])
        self.obj['paint'] = None

    def _polygon_check(self, polygon_list):
        """ polygon 의 시작 위치와 종료 위치를 이용하여 생성 조건을 반환한다.

        """
        if polygon_list is None or len(polygon_list) < 3:
            return False

        # 거리 계산
        dx = polygon_list[-1].x() - polygon_list[0].x()
        dy = polygon_list[-1].y() - polygon_list[0].y()
        d = dx * dx + dy * dy

        if d < self.mode.POLYGON_END_THRESHOLD:
            # 마지막 위치 수정
            del (polygon_list[-1])
            polygon_list.append(polygon_list[0])
            return True
        else:
            return False

    def _polygon_draw(self, polygon, attribute, id=-1):
        """ polygon 을 그린다.

            polygon 객체를 인수로 받아서 scene 에 추가한다.
        """
        # Call by Value
        attribute = attribute.copy()

        pen = QPen(self.mode.DRAW_PEN_COLOR, 3)
        if attribute['name'] in self.mode.POLYGON_BRUSH_COLOR:
            brush = QBrush(self.mode.POLYGON_BRUSH_COLOR[attribute['name']])
        else:
            brush = QBrush(self.mode.DRAW_BRUSH_COLOR)

        # polygon_item 생성
        polygon_item = PolygonItem(self, polygon, attribute, id)
        polygon_item.setPen(pen)
        polygon_item.setBrush(brush)

        # scene 에 추가
        self.items.append(polygon_item)
        self.scene.addItem(polygon_item)

        # polygon location
        self._polygon_location(polygon_item)

        # QGraphicPolygonItem 반환
        return polygon_item

    def _polygon_location(self, polygon_item):
        polygon = polygon_item.polygon
        attribute = polygon_item.attribute

        # Set text location
        text_locate, compare_list_y = [], []

        for i in range(len(polygon) - 1):
            compare_list_y.append(polygon[i].toPoint().y())
        top_of_polygon_y = min(compare_list_y)
        index = compare_list_y.index(top_of_polygon_y)

        text_locate.append(polygon[index].toPoint().x())
        text_locate.append(polygon[index].toPoint().y())
        text_locate[0] = text_locate[0] - 5
        text_locate[1] = text_locate[1] - 5

        # add text item
        if 'name' not in attribute:
            attribute['name'] = 'none'
        item = self.scene.addText(attribute['name'], QFont('Arial', 10))
        self.items.append(item)
        polygon_item.text_item = item
        item.setPos(text_locate[0], text_locate[1])

    def _polygon_add_info(self, polygon_item):
        """ polygon 을 metadata 에 추가한다.

        """
        region_attribute = polygon_item.attribute
        polygon = polygon_item.polygon

        xs = []
        ys = []
        for point in polygon:
            xs.append(int(point.x()))
            ys.append(int(point.y()))
        polygon_item.id = self.metadata.add_polygon(region_attribute, xs, ys)

    def _polygon_delete(self, polygon_item):
        # delete polygon
        # 1. remove metadata
        print('0')
        print(polygon_item.id)
        self.metadata.delete_polygon(polygon_item.id)

        # 2. remove text item
        if polygon_item.text_item is not None:
            self.items.remove(polygon_item.text_item)
            self.scene.removeItem(polygon_item.text_item)

        # 3. remove polygon
        self.items.remove(polygon_item)
        self.scene.removeItem(polygon_item)

    def _mask_draw(self):
        if self.image is None:
            return

        # QBitmap 생성
        bitmap = self.image.get_mask()

        # QPixmap 생성
        pixmap = QPixmap(self.pixmap)
        pixmap.fill(self.mode.DRAW_MASK_COLOR)

        # pixmap 에 Mask를 씌운다.
        pixmap.setMask(bitmap)

        # Item 생성 및 추가
        if self.obj['mask'] is not None:
            self.scene.removeItem(self.obj['mask'])
        self.obj['mask'] = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.obj['mask'])

    def _mask_reset(self):
        # Reset Mask
        if self.image is not None:
            self.image.reset_mask()

    def _paint_draw_sign(self, x, y):
        # draw paint sign
        brush = QBrush(self.mode.DRAW_MASK_COLOR) if self.mode.DRAW_PAINT_MODE else QBrush(QColor(255, 255, 255, 50))
        pen = QPen(QColor(0, 0, 0), 3)

        # Item 생성 및 추가
        width = self.mode.DRAW_PAINT_WIDTH
        if self.obj['paint'] is not None:
            self.scene.removeItem(self.obj['paint'])
        self.obj['paint'] = QGraphicsEllipseItem(int(x - width / 2), int(y - width / 2),
                                                 width, width)
        self.obj['paint'].setBrush(brush)
        self.obj['paint'].setPen(pen)
        self.scene.addItem(self.obj['paint'])

    def _draw_sequence_press(self, pos, out_of_range):
        """ view 에 item 들을 그린다.

            mode 로 view 에 그리는 방법을 다르게 설정 할 수 있다.
            press, move, release sequence 함수들은 서로 의존적이다.
            mousePressEvent 에서 호출된다.
        """
        if out_of_range:
            return

        last_pos = self.rect_p0
        self.rect_p0 = pos

        # Mode 1. polygon draw
        if self.mode.CURRENT == 1:
            # 새로운 위치를 지정 및 기억한다.
            polygon_list = self.obj['polygon']
            polygon_list.append(pos)

            # 조건을 확인하여 polygon 을 그린다.
            if self._polygon_check(polygon_list):
                # polygon list 를 이용하여 QPolygonF 객체 생성
                polygon = QPolygonF([QPointF(point) for point in polygon_list])

                # polygon 을 그린다.
                polygon_item = self._polygon_draw(polygon, self.mode.POLYGON_CURRENT_ATTRIBUTE)

                # metadata 추가 / id  할당
                self._polygon_add_info(polygon_item)

                # polygon list 정보 삭제
                polygon_list.clear()

                # lines 삭제
                self._delete_items(self.obj['lines'])

                # 좌표 초기화
                self.rect_p0 = None
                self.rect_p1 = None

            elif self.rect_p1 != None:
                # 임시 표시 직선을 그린다.
                pen = QPen(self.mode.DRAW_PEN_COLOR, self.mode.DRAW_PEN_WIDTH) if not out_of_range \
                    else QPen(self.mode.DRAW_PEN_COLOR_WARNNING, self.mode.DRAW_PEN_WIDTH)

                line = QLineF(self.rect_p0.x(), self.rect_p0.y(),
                              last_pos.x(), last_pos.y())
                self.obj['lines'].insert(0, self.scene.addLine(line, pen))

        # Mode 2. Magic Wand
        elif self.mode.CURRENT == 2:
            # option 설정
            if self.KEY_SHIFT and self.KEY_ALT:
                option = 'and'
            elif self.KEY_SHIFT:
                option = 'or'
            elif self.KEY_SHIFT:
                option = 'sub'
            else:
                option = 'select'

            # 현재 point mask 생성
            self.image.set_tolerance(self.mode.DRAW_MASK_TOLERANCE)
            self.image.set_mask(int(pos.x()), int(pos.y()), option=option)

            # mask 를 그린다.
            self._mask_draw()

        # Mode 3. Paint
        elif self.mode.CURRENT == 3:
            # paint or erase
            if self.mode.DRAW_PAINT_MODE:
                self.image.paint_mask(int(pos.x()), int(pos.y()), self.mode.DRAW_PAINT_WIDTH)
            else:
                self.image.erase_mask(int(pos.x()), int(pos.y()), self.mode.DRAW_PAINT_WIDTH)
            self._mask_draw()
            self._paint_draw_sign(int(pos.x()), int(pos.y()))

    def _draw_sequence_move(self, pos, out_of_range):
        """ view 에 item 들을 그린다.

            mouseMoveEvent 에서 호출된다.
        """

        # polygon draw
        if self.mode.CURRENT == 1:
            if self.rect_p0 is None:
                return
            else:
                self.rect_p1 = pos

            # QPen 선택
            pen = QPen(self.mode.DRAW_PEN_COLOR, self.mode.DRAW_PEN_WIDTH) if not out_of_range \
                else QPen(self.mode.DRAW_PEN_COLOR_WARNNING, self.mode.DRAW_PEN_WIDTH)

            # 마지막에 그렸던 직선 삭제
            if len(self.obj['lines']) > 0:
                self.scene.removeItem(self.obj['lines'][-1])
                del (self.obj['lines'][-1])

            # 새로운 직선을 그린다
            line = QLineF(self.rect_p0.x(), self.rect_p0.y(),
                          self.rect_p1.x(), self.rect_p1.y())
            self.obj['lines'].append(self.scene.addLine(line, pen))

        elif self.mode.CURRENT == 3 and not out_of_range:
            # paint or erase
            if self.KEY_MOUSE_LEFT:
                if self.mode.DRAW_PAINT_MODE:
                    self.image.paint_mask(int(pos.x()), int(pos.y()), self.mode.DRAW_PAINT_WIDTH)
                else:
                    self.image.erase_mask(int(pos.x()), int(pos.y()), self.mode.DRAW_PAINT_WIDTH)

                self._mask_draw()
            self._paint_draw_sign(int(pos.x()), int(pos.y()))

    def _mouse_check(self, e):
        """ 현재 좌표와 좌표가 이미지 위에 위치하는지 여부를 반환한다.

            Image 가 할당된 이후에 호출될 수 있어야 한다.
            QMouseEvent 가 주어져야한다.
        """
        assert self.image_item is not None, "No image to check"

        # 마우스 위치를 Scene 좌표로 변환한다.
        pos = self.mapToScene(e.pos())

        # 변환된 Scene 좌표를 item 좌표로 변환한다.
        pos = self.image_item.mapFromScene(pos)

        # image item 좌표 범위를 QRectF 클래스로 받아온다.
        rect = self.image_item.boundingRect()

        # 좌표와 좌표 위치 정보 반환.
        return pos, not rect.contains(pos)

    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if self.image is None:
            return

        if e.key() == Qt.Key_Escape:
            self.last_mask = self.image.backup_mask()
            self._mask_reset()
            self.refresh()
        if e.key() == Qt.Key_Shift:
            self.KEY_SHIFT = True
            self.mode.DRAW_PAINT_MODE = not self.mode.DRAW_PAINT_MODE
        if e.key() == Qt.Key_Alt:
            self.KEY_ALT = True
        if e.key() == Qt.Key_Control:
            self.KEY_CTRL = True
        if e.key() == Qt.Key_Space and self.image is not None:
            # Mask To Polygon (with backup)
            self.last_mask = self.image.backup_mask()
            polygon = self.image.get_polygon()
            if polygon is not None:
                polygon_item = self._polygon_draw(polygon, self.mode.POLYGON_CURRENT_ATTRIBUTE)
                self._polygon_add_info(polygon_item)
                self.last_polygon = polygon_item

                self._mask_reset()
                self.refresh()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Shift:
            self.KEY_SHIFT = False
        if e.key() == Qt.Key_Alt:
            self.KEY_ALT = False
        if e.key() == Qt.Key_Control:
            self.KEY_CTRL = False

    def showEvent(self, e):
        self._update()
        super().showEvent(e)

    def wheelEvent(self, e):
        if self.KEY_CTRL:
            if self.mode.CURRENT == 3:
                pos, out_of_range = self._mouse_check(e)
                if not out_of_range:
                    # pain wheel
                    self._paint_draw_sign(int(pos.x()), int(pos.y()))
            return

        # zoom in / out 구현
        if e.angleDelta().y() > 0 and self._zoom < 10:
            self.scale(1.25, 1.25)
            self._zoom += 1
        elif e.angleDelta().y() < 0 and self._zoom > -10:
            self.scale(0.8, 0.8)
            self._zoom -= 1

    def mousePressEvent(self, e):
        # QGraphicsView.ScrollHandDrag middle mouse
        super().mousePressEvent(e)

        if self.KEY_CTRL:
            return

        # 좌표와 정보를 받아온다.
        if self.image_item is not None:
            pos, out_of_range = self._mouse_check(e)
        else:
            return

        # Reset Mask
        if self.mode.CURRENT not in [0, 2, 3]:
            self._mask_reset()
            self._mask_draw()

        # Left Button
        if e.button() == Qt.LeftButton:
            self.KEY_MOUSE_LEFT = True

            # 좌표를 이용하여 view 를 그린다.
            self._draw_sequence_press(pos, out_of_range)

    def mouseMoveEvent(self, e):
        super().mouseMoveEvent(e)

        # Left Button
        if self.image_item is not None:
            # 좌표와 정보를 받아온다.
            pos, out_of_range = self._mouse_check(e)

            # 좌표를 이용하여 view 를 그린다.
            self._draw_sequence_move(pos, out_of_range)

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)

        # 좌표와 정보를 받아온다.
        if self.image_item is not None:
            pos, out_of_range = self._mouse_check(e)
        else:
            return

        # Left Button
        if e.button() == Qt.LeftButton:
            self.KEY_MOUSE_LEFT = False