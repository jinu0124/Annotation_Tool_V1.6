class ImageInfo:
    def __init__(self, filename, filesize):
        self.filename = filename
        self.fileref = ""
        self.size = filesize
        self.id = str(self.filename) + str(self.size)
        self.base64_img_data = ""
        self.regions = []
        self.polygon_count = 0

    def add_polygon(self, region, xs, ys):
        # polygons는 list 형식으로 저장한다.
        # 개별 polygon 정보는 region, xs, ys 정보를 담은 dict 형식으로 저장한다.
        # region attribute는 dictionary
        if region == None or xs == None or ys == None:
            return
        if len(xs) != len(ys) or len(xs) < 3:
            return
        self.regions.append({"name": "polygon", "region": region, "xs": xs, "ys": ys, "id": self.polygon_count})
        self.polygon_count += 1
        return self.polygon_count - 1

    def delete_polygon(self, id):
        for region in self.regions:
            if region["id"] == id:
                self.regions.remove(region)
                self.polygon_count -= 1
                break

    def out_polygons_to_csv(self):
        regions = []

        for reg in self.regions:
            if reg["name"] != 'polygon':
                continue
            xs = reg['xs']
            ys = reg['ys']
            region = reg['region']

            xmin = min(xs)
            xmax = max(xs)
            ymin = min(ys)
            ymax = max(ys)
            width = 800
            height = 600

            shape = [self.filename, width, height, region['name'], xmin, ymin, xmax, ymax]
            regions.append(shape)
        return regions

    def out_polygons_to_dict(self):
        # VGG annotation tool type, json 변환용 dictionary 반환
        regions = dict()
        top = 0
        # regions attribute
        for reg in self.regions:
            if reg["name"] != "polygon":
                continue
            xs = reg["xs"]
            ys = reg["ys"]
            region = reg["region"]

            shape = {"name": "polygon", "all_points_x": xs, "all_points_y": ys}
            regions[str(top)] = {"shape_attributes": shape, "region_attributes": region}
            top += 1

        key = self.id
        img_dict = {"fileref": self.fileref,
                    "size": self.size,
                    "filename": self.filename,
                    "base64_img_data": self.base64_img_data,
                    "file_attributes": {},
                    "regions": regions
                    }

        return key, img_dict

    def out_polygons_to_list(self):
        # list 형식의 polygon 반환
        polygons = []
        id = 0
        for reg in self.regions:
            if reg["name"] != "polygon":
                continue
            all_points_x = reg["xs"]
            all_points_y = reg["ys"]
            region = reg["region"]
            polygon = [region, all_points_x, all_points_y, id]
            polygons.append(polygon)
            id += 1

        return polygons

    def import_json_data(self, json_data):
        # json data 를 현재 metadata 정보에 추가.
        regions = json_data['regions']

        # load polygon
        for idx in range(len(regions)):
            if regions[str(idx)]["shape_attributes"]["name"] != "polygon":
                continue
            xs = regions[str(idx)]["shape_attributes"]["all_points_x"]
            ys = regions[str(idx)]["shape_attributes"]["all_points_y"]
            region = regions[str(idx)]["region_attributes"]
            self.add_polygon(region, xs, ys)