import qt_option
import os
import json
import test
import pandas as pd

from pysys import dataset
from widget import qt_load, qt_image, qt_central, qt_merge

from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QDesktopWidget, QFileDialog
from PyQt5.QtGui import QIcon


class ToolWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dataset = None

        self.json_data = {}
        self.json_path = []

        # Edit Mode 생성
        self.mode = qt_option.EditMode()

        # Widget 생성
        self.central_widget = qt_central.CentralWidget(self.mode)
        self.setCentralWidget(self.central_widget)
        self.image_widget = self.central_widget.image_widget
        self.leftside_widget = self.central_widget.leftside_widget

        # Action 생성
        self._create_action()

        # Menu 생성
        self._create_menu()

        # Toolbar 생성
        self._create_toolbar()

        # Connect
        self._connect()

        # Status Bar 생성
        self.statusBar().showMessage('Ready')

        # UI Title 설정
        self.setWindowTitle('PyQt5 Image Annotation Tool')

        # Icon 설정
        self.setWindowIcon(QIcon("./icon/icon.png"))

        # UI Size 설정
        self.resize(1280, 960)

        # UI 출력
        self.show()
        self._center()

        #
        self.activateWindow()

    def load_data(self, dataset):
        if dataset.image_count < 1:
            return
        self.dataset = dataset
        self.image_widget.load_data(dataset)
        self.leftside_widget.load_filelist(dataset)
        self.dataset.import_json_dict(self.json_data)

    def load_json(self):
        # json data 초기화
        self.json_data.clear()

        # file 하나 불러오기
        options = QFileDialog.Options()  # json file finder 열기
        options |= QFileDialog.ShowDirsOnly

        json_file_dirs = QFileDialog.getOpenFileNames(self,
                         "Open Json File", filter = "json(*.json)")
        json_file_dirs = json_file_dirs[0]

        for dir in json_file_dirs:
            # load 실패
            if not os.path.exists(dir):
                return super()

        # 취소
        if len(json_file_dirs) < 1:
            return super()

        # Load 경로 저장
        elif len(json_file_dirs) == 1:
            self.json_path = json_file_dirs

        for json_file_dir in json_file_dirs:
            with open(json_file_dir, 'r') as LD_json:
                loaded_json_file = json.load(LD_json)

            # Main Window 에 load된 json 파일 병합.
            self.json_data.update(loaded_json_file)

        # dataset 에 추가.
        if self.dataset is not None:
            self.dataset.reset()
            self.dataset.import_json_dict(self.json_data)

            # image redraw
            self.image_widget.redraw()

            # self.leftside_widget.add_attr_list() #***********************************************************************

    def save_csv(self, path = ""):
        if self.dataset is None:
            return

        image_list = self.dataset.out_metadata_to_csv()
        csv_data = pd.DataFrame(image_list)
        csv_data.columns = ['filename', 'width', 'height', 'class', 'xmin', 'ymin', 'xmax', 'ymax']

        CSV_DIR = path
        if path == "":
            CSV_DIR = os.getcwd()
            csv_data.to_csv(CSV_DIR + '/new_csv.csv', index=None, na_rep='NaN', encoding='utf-8')
        else:
            csv_data.to_csv(CSV_DIR, index=None, na_rep='NaN', encoding='utf-8')

    def save_new_csv(self):
        if self.dataset is None:
            return

        path = QFileDialog.getSaveFileName(self, 'Save csv File', filter="csv(*.csv)")
        path = path[0]

        if path:
            self.save_csv(path)
        else:
            return super()

    def save_json(self, path = ""):
        if self.dataset is None:
            return

        if path == "" and (len(self.json_path) != 1 or \
           not os.path.exists(self.json_path[0])):
            self.save_new_json()
            return
        elif path == "":
            path = self.json_path[0]

        dict_info = self.dataset.out_metadata_to_dict()
        JSON_DIR = path

        if os.path.exists(JSON_DIR) is True: # 이미 존재하면 합치기
            json_annotation = json.load(open(JSON_DIR))
            json_annotation.update(dict_info)
            dict_info = json_annotation

        with open(JSON_DIR, 'w') as outfile:
            json.dump(dict_info, outfile, indent = '\t')

        self.json_path.clear()
        self.json_path = [path]

    def save_new_json(self):
        if self.dataset is None:
            return

        path = QFileDialog.getSaveFileName(self, 'Save Json File', filter = "json(*.json)")
        path = path[0]

        if path:
            self.save_json(path)
        else:
            return super()

    def cancel_json(self):
        if len(self.json_data) > 0:
            self.dataset.cancel_json_dict()
            for i in self.json_data:
                self.json_data[i]['regions'] = []
            super()
        else:
            return super()

    def calibration(self):
        print('calibration')

    def merge_json(self):
        merge_win = qt_merge.MergeDialog()
        merge_win.showModal()

    def _create_action(self):
        self.action = {}

        # Exit Action
        exitAction = QAction(QIcon(':/icon/exit.png'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)
        self.action['exit'] = exitAction

        loadAction = QAction('Load', self)
        loadAction.setShortcut('Ctrl+L')
        loadAction.setStatusTip('Load Image File')
        loadAction.triggered.connect(self._action_load_image)
        self.action['load'] = loadAction

        selectMode0 = QAction(QIcon(':/icon/hand.png'), 'Select/Search', self)
        selectMode0.setShortcut('1')
        selectMode0.setStatusTip('Select/Search')
        selectMode0.triggered.connect(lambda x: [self.mode.set_mode(0), self.image_widget.view.refresh()])
        self.action['mode0'] = selectMode0

        selectMode1 = QAction(QIcon(':/icon/polygon.png'), 'Draw Polygon', self)
        selectMode1.setShortcut('2')
        selectMode1.setStatusTip('Draw Polygon')
        selectMode1.triggered.connect(lambda x: [self.mode.set_mode(1), self.image_widget.view.refresh()])
        self.action['mode1'] = selectMode1

        selectMode2 = QAction(QIcon(':/icon/contour.png'), 'Magic Wand', self)
        selectMode2.setShortcut('3')
        selectMode2.setStatusTip('Magic Wand')
        selectMode2.triggered.connect(lambda x: [self.mode.set_mode(2), self.image_widget.view.refresh()])
        self.action['mode2'] = selectMode2

        selectMode3 = QAction(QIcon(':/icon/paint.png'), 'Paint Mask', self)
        selectMode3.setShortcut('4')
        selectMode3.setStatusTip('Paint Mask')
        selectMode3.triggered.connect(lambda x: [self.mode.set_mode(3), self.image_widget.view.refresh()])
        self.action['mode3'] = selectMode3

        nextImage = QAction(QIcon(':/icon/next.png'), 'Next', self)
        nextImage.setShortcut('E')
        nextImage.setStatusTip('Select Next Image')
        nextImage.triggered.connect(lambda x: self.image_widget.next_image())
        self.action['next'] = nextImage

        prevImage = QAction(QIcon(':/icon/prev.png'), 'Prev', self)
        prevImage.setShortcut('W')
        prevImage.setStatusTip('Select Previous Image')
        prevImage.triggered.connect(lambda x: self.image_widget.prev_image())
        self.action['prev'] = prevImage

        importJson = QAction(QIcon(':/icon/import_json.png'), '&Import JSON..', self)
        importJson.setShortcut('Ctrl+J')
        importJson.setStatusTip('Import JSON File')
        importJson.triggered.connect(self.load_json)
        self.action['import'] = importJson

        saveJson = QAction(QIcon(':/icon/save.png'), '&Save', self)
        saveJson.setShortcut('Ctrl+S')
        saveJson.setStatusTip('Save JSON File')
        saveJson.triggered.connect(lambda x: self.save_json())
        self.action['saveJSON'] = saveJson

        saveNewJson = QAction(QIcon(':/icon/saveas.png'), '&Save As..', self)
        saveNewJson.setShortcut('Ctrl+Shift+S')
        saveNewJson.setStatusTip('Save New JSON File')
        saveNewJson.triggered.connect(self.save_new_json)
        self.action['saveAs'] = saveNewJson

        mergeJson = QAction(QIcon(':/icon/merge_json.png'), '&Merge Json', self)
        mergeJson.setShortcut('Ctrl+M')
        mergeJson.setStatusTip('Merge Json File')
        mergeJson.triggered.connect(self.merge_json)
        self.action['merge'] = mergeJson

        cancelJson = QAction(QIcon(':/icon/cancel_json.png'), '&Cancel JSON', self)
        cancelJson.setStatusTip('cancel')
        cancelJson.triggered.connect(self.cancel_json)
        self.action['cancel'] = cancelJson

        calibration = QAction(QIcon(':/icon/calibration.png'), '&Image Calibration', self)
        calibration.setStatusTip('Create New Calibrate Image')
        calibration.triggered.connect(self.calibration)
        self.action['calibration'] = calibration

        undoMask = QAction('Undo', self)
        undoMask.setShortcut('Ctrl+Z')
        undoMask.setStatusTip('Restore last mask')
        undoMask.triggered.connect(self.image_widget.view.restore)
        self.action['undo'] = undoMask

        csv = QAction(QIcon(':/icon/savecsv.png'), '&Save CSV', self)
        csv.setStatusTip('CSV')
        csv.triggered.connect(lambda x:self.save_csv())
        self.action['SaveCSV'] = csv

        csvas = QAction(QIcon(':/icon/savecsvas.png'), '&Save CSV As..', self)
        csvas.setStatusTip('Save CSV As..')
        csvas.triggered.connect(self.save_new_csv)
        self.action['SaveCSVAs'] = csvas

    def _create_menu(self):
        # menubar 생성.
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)

        # File
        filemenu = menubar.addMenu('&File')
        filemenu.addAction(self.action['load'])
        filemenu.addAction(self.action['saveJSON'])
        filemenu.addAction(self.action['saveAs'])
        filemenu.addAction(self.action['SaveCSV'])
        filemenu.addAction(self.action['SaveCSVAs'])
        filemenu.addAction(self.action['import'])
        filemenu.addAction(self.action['cancel'])
        filemenu.addAction(self.action['exit'])

        # Edit
        editmenu = menubar.addMenu('&Edit')
        editmenu.addAction(self.action['mode0'])
        editmenu.addAction(self.action['mode1'])
        editmenu.addAction(self.action['mode2'])
        editmenu.addAction(self.action['mode3'])
        editmenu.addAction(self.action['prev'])
        editmenu.addAction(self.action['next'])
        editmenu.addAction(self.action['undo'])

        # Tools
        toolmenu = menubar.addMenu('&Tools')
        toolmenu.addAction(self.action['merge'])
        toolmenu.addAction(self.action['calibration'])

    def _create_toolbar(self):
        # toolbar 생성
        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(self.action['saveJSON'])
        self.toolbar.addAction(self.action['saveAs'])
        self.toolbar.addAction(self.action['prev'])
        self.toolbar.addAction(self.action['next'])
        self.toolbar.addAction(self.action['exit'])
        self.toolbar.addAction(self.action['mode0'])
        self.toolbar.addAction(self.action['mode1'])
        self.toolbar.addAction(self.action['mode2'])
        self.toolbar.addAction(self.action['mode3'])

    def _connect(self):
        # Attribute Config 선언 & click event
        R, G, B = 'RED', 'GREEN', 'BLUE'
        self.leftside_widget.pushButton.clicked.connect(self.leftside_widget.color_select)
        self.leftside_widget.pushButton_2.clicked.connect(lambda: self.leftside_widget.fast_color(R))
        self.leftside_widget.pushButton_3.clicked.connect(lambda: self.leftside_widget.fast_color(G))
        self.leftside_widget.pushButton_4.clicked.connect(lambda: self.leftside_widget.fast_color(B))
        self.leftside_widget.pushButton_5.clicked.connect(self.leftside_widget.add_attr_list)
        self.leftside_widget.pushButton_6.clicked.connect(self.leftside_widget.del_attr_list)
        self.leftside_widget.listWidget_2.itemDoubleClicked.connect(self.leftside_widget.select_attr_list)
        self.leftside_widget.listWidget.itemDoubleClicked.connect(lambda: self.leftside_widget.select_image(self.image_widget))

        # Tolerance Control
        self.leftside_widget.horizontalSlider.valueChanged.connect(self.leftside_widget.tolerance_ctrl)
        self.leftside_widget.lineEdit_2.returnPressed.connect(self.leftside_widget.tolerance_input)

        # Paint Size Control
        self.leftside_widget.horizontalSlider_2.valueChanged.connect(self.leftside_widget.paint_ctrl)
        self.leftside_widget.lineEdit_3.returnPressed.connect(self.leftside_widget.paint_input)

    def _center(self):
        # 창을 화면 가운데에 위치시킨다.
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _action_load_image(self):
        load_win = qt_load.LoadDialog()

        # accept되면 1, reject되면 0
        r = load_win.showModal()

        if r:
            text = load_win.image_files
            LD_image = text

            image_data = dataset.DirectDataset(LD_image)
            self.load_data(image_data)
        else:
            # Cancel
            return super()

    ##pip install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
    ##pyinstaller -F -n myname.exe widget.py --noconsole
    ##https://icoconvert.com/