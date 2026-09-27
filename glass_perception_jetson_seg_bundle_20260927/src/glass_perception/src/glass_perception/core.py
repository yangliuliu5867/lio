"""ROS/model-independent temporal gate. Association does not assume class identity."""
import math
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Detection:
    label: str
    confidence: float
    box: tuple
    polygon: tuple = ()


def label_map(names, target_labels):
    """Map explicitly configured model labels to one downstream candidate type."""
    if not isinstance(target_labels, list) or not target_labels:
        raise ValueError('target_labels must be a nonempty list')
    wanted = {str(name).strip().lower() for name in target_labels}
    if '' in wanted:
        raise ValueError('empty target label')
    items = names.items() if isinstance(names, dict) else enumerate(names)
    available = {int(i): str(name).strip().lower() for i, name in items}
    missing = wanted - set(available.values())
    if missing:
        raise ValueError('Requested labels absent from weights: '+', '.join(sorted(missing)))
    return {i: 'suspect_surface' for i, name in available.items() if name in wanted}


def clean(detection, width, height):
    if width <= 0 or height <= 0:
        raise ValueError('image dimensions must be positive')
    if detection.label != 'suspect_surface' or len(detection.box) != 4:
        raise ValueError('invalid detection label/box')
    values = (*detection.box, detection.confidence)
    if not all(math.isfinite(v) for v in values) or not 0 <= detection.confidence <= 1:
        raise ValueError('nonfinite detection or invalid confidence')
    x1, y1, x2, y2 = detection.box
    box = (max(0., min(width, x1)), max(0., min(height, y1)),
           max(0., min(width, x2)), max(0., min(height, y2)))
    if box[2] <= box[0] or box[3] <= box[1]:
        raise ValueError('empty/inverted box')
    polygon = []
    for point in detection.polygon:
        if len(point) != 2 or not all(math.isfinite(v) for v in point):
            raise ValueError('invalid polygon')
        polygon.append((max(0., min(width, point[0])), max(0., min(height, point[1]))))
    if polygon and len(polygon) < 3:
        raise ValueError('polygon needs at least three vertices')
    return Detection(detection.label, detection.confidence, box, tuple(polygon))


def iou(a, b):
    intersection = max(0., min(a[2], b[2])-max(a[0], b[0])) * max(0., min(a[3], b[3])-max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
    return intersection / union if union > 0 else 0.


@dataclass
class Track:
    box: tuple
    last_seen: float
    hits: int = 0
    votes: deque = field(default_factory=deque)


class TemporalGate:
    def __init__(self, min_hits=3, window=5, min_mean_confidence=0.4, match_iou=0.3, ttl=0.5):
        if type(min_hits) is not int or type(window) is not int or not 1 <= min_hits <= window:
            raise ValueError('require integer 1 <= min_hits <= window')
        if not all(math.isfinite(v) for v in (min_mean_confidence, match_iou, ttl)):
            raise ValueError('nonfinite gate parameter')
        if not 0 < min_mean_confidence <= 1 or not 0 < match_iou <= 1 or ttl <= 0:
            raise ValueError('invalid gate parameter range')
        self.min_hits, self.window = min_hits, window
        self.min_mean_confidence = min_mean_confidence
        self.match_iou, self.ttl = match_iou, ttl
        self.tracks, self.next_id, self.last_stamp = {}, 1, None

    def update(self, detections, stamp, width, height):
        if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
            raise ValueError('image dimensions must be positive integers')
        if not math.isfinite(stamp) or stamp < 0:
            raise ValueError('invalid acquisition timestamp')
        if self.last_stamp is not None and stamp <= self.last_stamp:
            raise ValueError('duplicate/out-of-order frame')
        detections = [clean(d, width, height) for d in detections]
        self.last_stamp = stamp
        self.tracks = {k: t for k, t in self.tracks.items() if stamp-t.last_seen <= self.ttl}
        pairs = sorted(((iou(t.box, d.box), k, j) for k, t in self.tracks.items()
                        for j, d in enumerate(detections)), reverse=True)
        assigned, used = {}, set()
        for overlap, k, j in pairs:
            if overlap >= self.match_iou and k not in used and j not in assigned:
                assigned[j] = k
                used.add(k)
        for k, t in self.tracks.items():
            if k not in used:
                t.hits = 0
                t.votes.append(None)
                while len(t.votes) > self.window:
                    t.votes.popleft()
        output = []
        for j, d in enumerate(detections):
            k = assigned.get(j)
            if k is None:
                k = self.next_id
                self.next_id += 1
                self.tracks[k] = Track(d.box, stamp)
            t = self.tracks[k]
            t.box, t.last_seen, t.hits = d.box, stamp, t.hits + 1
            t.votes.append(d.confidence)
            while len(t.votes) > self.window:
                t.votes.popleft()
            evidence = list(t.votes)
            # Missing processed frames contribute zero, not fabricated observations.
            mean_confidence = sum(v if v is not None else 0. for v in evidence) / len(evidence)
            output.append(dict(track_id=k, detection=d, mean_confidence=mean_confidence,
                               consecutive_hits=t.hits,
                               stable=t.hits >= self.min_hits and
                               mean_confidence >= self.min_mean_confidence))
        return output
