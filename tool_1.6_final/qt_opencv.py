import cv2 as cv
import numpy as np
from PyQt5.QtGui import QImage, QBitmap, QPolygonF
from PyQt5.QtCore import QPointF


class OpenCVImage():
    def __init__(self, image, connectivity=4, tolerance=35):
        self._image = image
        self._origin = image

        # magic wand
        height, width = self._image.shape[:2]
        self._mask = np.zeros((height, width), dtype=np.uint8)
        self._flood_mask = np.zeros((height + 2, width + 2), dtype=np.uint8)
        self.connectivity = connectivity
        self.tolerance = None
        self.set_tolerance(tolerance)
        self._flood_fill_flags = (
                self.connectivity | cv.FLOODFILL_FIXED_RANGE | cv.FLOODFILL_MASK_ONLY | 255 << 8
        )  # 255 << 8 tells to fill with the value 255

    def reset_image(self):
        self._image = self._origin

    def reset_mask(self):
        height, width = self._image.shape[:2]
        self._mask = np.zeros((height, width), dtype=np.uint8)

    def backup_mask(self):
        return self._mask.copy()

    def restore_mask(self, mask):
        assert self._mask.shape == mask.shape, "Shape mismatch between masks"
        self._mask = mask.copy()

    def set_tolerance(self, value):
        self.tolerance = (value,) * 3

    def set_connectivity(self, value):
        self.connectivity = value

    def set_mask(self, x, y, option='or'):
        self._flood_mask[:] = 0
        cv.floodFill(
            self._image,
            self._flood_mask,
            (x, y),
            0,
            self.tolerance,
            self.tolerance,
            self._flood_fill_flags,
        )
        flood_mask = self._flood_mask[1:-1, 1:-1].copy()

        if option == 'and':
            self._mask = cv.bitwise_and(self._mask, flood_mask)
        elif option == 'or':
            self._mask = cv.bitwise_or(self._mask, flood_mask)
        elif option == 'sub':
            self._mask = cv.bitwise_and(self._mask, cv.bitwise_not(flood_mask))
        else:
            self._mask = flood_mask

    def get_image(self):
        # RGB 형식으로 변환
        image = cv.cvtColor(self._image, cv.COLOR_BGR2RGB)

        # QImage 생성 및 반환
        height, width = image.shape[:2]
        return QImage(image, width, height, QImage.Format_RGB888)

    def get_mask(self):
        # Mask 생성. QBitmap 변환을 위해서 not 연산
        mask = cv.bitwise_not(self._mask)

        # QImage 로 변환하기위해 convert color
        mask = cv.cvtColor(mask, cv.COLOR_BGR2RGB)

        # QImage 생성
        height, width = self._mask.shape[:2]
        mono = QImage(mask, width, height, QImage.Format_RGB888)

        # QBitmap 생성
        bitmap = QBitmap(width, height).fromImage(mono)
        return bitmap

    def get_polygon(self):
        contours, hierarchy = cv.findContours(self._mask, cv.RETR_CCOMP, cv.CHAIN_APPROX_NONE)
        if len(contours) < 1:
            return None

        # 현재는 최대 크기 polygon 만을 반환.
        # index = contours.index(max(contours, key=lambda x: cv.contourArea(x)))

        key = np.array([cv.contourArea(contour) for contour in contours])
        index = np.argmax(key)
        x = contours[index][:, 0][:, 0].tolist()
        y = contours[index][:, 0][:, 1].tolist()

        # hierarchy : [Next, Previous, First_Child, Parent]
        if hierarchy[0][index][2] != -1:
            # Child 가 존재할 경우
            x.extend(contours[hierarchy[0][index][2]][:, 0][:, 0].tolist())
            y.extend(contours[hierarchy[0][index][2]][:, 0][:, 1].tolist())

        elif hierarchy[0][index][3] != -1:
            # Parent 가 존재할 경우
            x = contours[hierarchy[0][index][2]][:, 0][:, 0].tolist() + x
            y = contours[hierarchy[0][index][2]][:, 0][:, 1].tolist() + y

        # Create Polygon
        polygon = QPolygonF()
        for idx in range(len(x)):
            polygon.append(QPointF(x[idx], y[idx]))

        return polygon

    def paint_mask(self, x, y, width):
        m_height, m_width = self._mask.shape[:2]
        assert x >= 0 and x < m_width \
               and y >= 0 and y < m_height, "Invalid paint position"
        cv.circle(self._mask, center=(x, y), radius=int(width / 2), color=255, thickness=-1)

    def erase_mask(self, x, y, width):
        m_height, m_width = self._mask.shape[:2]
        assert x >= 0 and x < m_width \
               and y >= 0 and y < m_height, "Invalid erase position"
        cv.circle(self._mask, center=(x, y), radius=int(width / 2), color=0, thickness=-1)

    def grayscale(self):
        # gray scale
        self._image = cv.cvtColor(self._image, cv.COLOR_BGR2GRAY)

        # hist
        self._image = cv.equalizeHist(self._image)

    def crack_detector_opening(self, opening_kernel_size):
        # parameters
        SUBTRACTION_THRESHOLD_VALUE = 20
        MEDIAN_FILTER_SIZE = 39
        MORPHOLOGICAL_OPENING_KERNEL_SIZE = opening_kernel_size

        # step 1. gray scale image
        image = self._image
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

        # step 2. median filter on image
        gray = image.copy()
        image = cv.medianBlur(image, MEDIAN_FILTER_SIZE)

        # step 3. image subtraction
        image = cv.subtract(image, gray)

        # additional processing : morphological opening
        if opening_kernel_size > 0:
            opening_kernel = np.ones((MORPHOLOGICAL_OPENING_KERNEL_SIZE, MORPHOLOGICAL_OPENING_KERNEL_SIZE), np.uint8)
            image = cv.morphologyEx(image, cv.MORPH_OPEN, opening_kernel)

        # step 4. improved subtraction processing
        image = image + image * (image > SUBTRACTION_THRESHOLD_VALUE)

        self._image = image

    def crack_detector(self, opening_kernel_size, closing_kernel_size):
        """ 이미지 전처리를 통해서 균열을 찾는다.

            논문 "INTELIGENT CRACK DETECTING ALGORITHM ON THE CONCRETE
                CRACK IMAGE USING NEURAL NETWORK, Hyeong-Gyeong Moon and Jung-Hoon Kim" 참조
        """
        # parameters
        GAUSSIAN_FILTER_SIZE = 5
        GAUSSIAN_FILTER_SIG = 0.5
        MORPHOLOGICAL_CLOSING_KERNEL_SIZE = closing_kernel_size

        # step 1, 2, 3, 4...
        self.crack_detector_opening(opening_kernel_size)

        # step 5. gaussian filtering (low-pass filter)
        image = self._image
        image = cv.GaussianBlur(image, (GAUSSIAN_FILTER_SIZE, GAUSSIAN_FILTER_SIZE),
                                GAUSSIAN_FILTER_SIG)

        # step 6. create binary image by using Otsu method
        _, image = cv.threshold(image, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

        # step 7. morphological closing
        closing_kernel = np.ones((MORPHOLOGICAL_CLOSING_KERNEL_SIZE, MORPHOLOGICAL_CLOSING_KERNEL_SIZE), np.uint8)
        image = cv.morphologyEx(image, cv.MORPH_CLOSE, closing_kernel)

        self._image = image

    def edge_detector(self, canny_min, canny_max):
        MEDIAN_FILTER_SIZE = 5

        # step 1. gray scale image
        image = self._image
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

        # step 2. equalize histogram
        image = cv.equalizeHist(image)

        # step 3. median filter
        image = cv.medianBlur(image, MEDIAN_FILTER_SIZE)

        # step 4. canny edge detect
        image = cv.Canny(image, canny_min, canny_max)

        self._image = image
