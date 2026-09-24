"""Ultralytics adapter, loaded only when inference is requested."""
from pathlib import Path
from .core import Detection, label_map


class YoloBackend:
    def __init__(self, weights, target_labels, confidence=0.25, nms_iou=0.5,
                 imgsz=640, device='cpu', max_det=50):
        if not weights or not Path(weights).expanduser().is_file():
            raise ValueError('Supply an existing trained suspect-surface weights file')
        if not 0 < confidence <= 1 or not 0 < nms_iou <= 1:
            raise ValueError('confidence and nms_iou must be in (0,1]')
        if type(imgsz) is not int or imgsz <= 0 or type(max_det) is not int or max_det <= 0:
            raise ValueError('imgsz and max_det must be positive integers')
        from ultralytics import YOLO
        self.model = YOLO(str(Path(weights).expanduser()))
        if self.model.task not in ('detect', 'segment'):
            raise ValueError('Only detect/segment weights supported')
        self.labels = label_map(self.model.names, target_labels)
        self.options = dict(conf=confidence, iou=nms_iou, imgsz=imgsz,
                            device=device, max_det=max_det, verbose=False,
                            classes=list(self.labels), agnostic_nms=True)

    def predict(self, image):
        result = self.model.predict(source=image, **self.options)[0]
        if result.boxes is None:
            return []
        polygons = result.masks.xy if result.masks is not None else None
        output = []
        for i, (box, confidence, class_id) in enumerate(zip(
                result.boxes.xyxy.cpu().tolist(), result.boxes.conf.cpu().tolist(),
                result.boxes.cls.cpu().tolist())):
            polygon = ()
            if polygons is not None and len(polygons[i]) >= 3:
                polygon = tuple(tuple(map(float, p)) for p in polygons[i])
            output.append(Detection(self.labels[int(class_id)], float(confidence),
                                    tuple(map(float, box)), polygon))
        return output
