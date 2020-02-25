import os
import glob
import cv2 as cv
from pysys import metadata


class Dataset:
    def __init__(self, source):
        self.source = source

        self.image_count = 0
        self.image_dirs = None
        self._image_info = []
        self._load_source(source)

    def reset(self):
        self.image_count = 0
        self._image_info = []
        self._load_source(self.source)

    def load_image(self, image_id):
        """ 지정된 번호의 이미지와 정보를 반환한다.

            opencv, numpy array 형식의 이미지를 반환한다.
            Default 설정으로는 디렉토리 경로를 이용해 불러온다.
            이미지를 불러오는 방법은 재정의 될 수 있다.
        """
        assert image_id < self.image_count, "Invalid image id"

        image = cv.imread(self.image_dirs[image_id])
        return image, self._image_info[image_id]

    def cancel_json_dict(self):
        for image_info in self._image_info:
            image_info.regions = []

    def out_metadata_to_csv(self):
        """CSV로 저장될 수 있는 dict 형태로 image_info 반환

        """
        image_list = []
        image_sort_list = []

        #metadata.out_polygons_to_csv
        for image_info in self._image_info:
            image_value = image_info.out_polygons_to_csv()
            if len(image_value) >= 1:
                image_list.append(image_value)

        #list sorting
        for i in range(len(image_list)):
            for j in range(len(image_list[i])):
                reduce_dimension = image_list[i][j]
                image_sort_list.append(reduce_dimension)

        return image_sort_list

    def out_metadata_to_dict(self):
        """ json 으로 저장될 수 있는 dictionary 형태로 image_info 반환

        """
        json_dict = dict()
        for image_info in self._image_info:
            key, image_dict = image_info.out_polygons_to_dict()  # key : image 이름 + size, img_dictionary
            json_dict[key] = image_dict

        return json_dict

    def import_json_dict(self, json_dict):
        """ json dictionary 를 인수로 받아 image info 를 수정한다.

            json dict 의 key 값은 filename + filesize 이다.
            json dict key 와 image_info id 를 비교하여 update 한다.
            dataset 에 일치하는 id 가 없을 경우, 해당 json 정보는 무시된다.
        """
        keys = json_dict.keys()

        for image_info in self._image_info:
            if image_info.id not in keys:
                continue
            image_info.import_json_data(json_dict[image_info.id])

    def _load_source(self, source):
        """ 데이터 소스를 불러와 Dataset을 초기화한다.

            Default 설정으로는 디렉토리 경로를 이용해 불러온다.
            데이터베이스 또는 다른 방법의 구현하고자 한다면,
            load_source method를 override 하여 사용할 수 있다.
            image_count와 image_info를 초기화 한다.
        """
        self.image_dirs = glob.glob(source + '/*.jpg')
        self._call_by_directory()

    def _call_by_directory(self):
        """ 데이터 소스를 디렉토리 경로로 이용해 불러온다.

            source 에 이미지가 저장된 디렉토리가 넘어와야 한다.
        """

        # 디렉토리의 jpg 파일을 불러온다.
        self.image_count = len(self.image_dirs)

        self._image_info = []
        for image_dir in self.image_dirs:
            filename = os.path.basename(image_dir)
            filesize = os.path.getsize(image_dir)
            self._image_info.append(metadata.ImageInfo(filename, filesize))


class DirectDataset(Dataset):
    def __init__(self, source):
        super().__init__(source)

    def _load_source(self, source):
        self.image_dirs = source
        self._call_by_directory()