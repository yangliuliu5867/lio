#!/usr/bin/env python3
"""Image-only ROS adapter. Latest-frame queue avoids accumulated inference lag."""
import math
import threading
import time

import cv2
import rospy
from cv_bridge import CvBridge
from geometry_msgs.msg import Point32
from sensor_msgs.msg import Image
from glass_perception.msg import SurfaceCandidate, SurfaceCandidateArray
from glass_perception.backend import YoloBackend
from glass_perception.core import TemporalGate


class SurfaceDetector:
    def __init__(self):
        self.gate_options = rospy.get_param('~temporal', {})
        self.gate = TemporalGate(**self.gate_options)
        self.rate = float(rospy.get_param('~rate_hz', 10.0))
        self.max_age = float(rospy.get_param('~max_image_age_s', 0.5))
        if not all(math.isfinite(v) and v > 0 for v in (self.rate, self.max_age)):
            raise ValueError('rate_hz/max_image_age_s must be finite and positive')
        self.backend = YoloBackend(
            rospy.get_param('~weights', ''),
            rospy.get_param('~target_labels', ['suspect_surface']),
            **rospy.get_param('~inference', {}))
        self.bridge = CvBridge()
        self.lock = threading.Lock()
        self.pending = None
        self.last_clock = None
        self.stream_key = None
        self.pub = rospy.Publisher('~candidates', SurfaceCandidateArray, queue_size=1)
        self.debug = rospy.Publisher('~debug_image', Image, queue_size=1)
        self.sub = rospy.Subscriber(rospy.get_param('~image_topic', '/camera/color/image_raw'),
                                    Image, self.receive, queue_size=1, buff_size=2**24)
        self.timer = rospy.Timer(rospy.Duration(1.0/self.rate), self.process, reset=True)
        rospy.loginfo('Suspect-surface image-only detector ready; stable does NOT mean physically confirmed')

    def receive(self, message):
        with self.lock:
            self.pending = message

    def process(self, _event):
        now = rospy.Time.now().to_sec()
        if self.last_clock is not None and now < self.last_clock:
            self.gate = TemporalGate(**self.gate_options)
        self.last_clock = now
        with self.lock:
            message, self.pending = self.pending, None
        if message is None:
            return
        stamp = message.header.stamp.to_sec()
        if stamp <= 0 or now-stamp > self.max_age or stamp-now > 0.05:
            rospy.logwarn_throttle(2., 'Dropping stale/future/unstamped image')
            return
        try:
            stream_key = (message.header.frame_id, message.width, message.height)
            if stream_key != self.stream_key:
                self.gate = TemporalGate(**self.gate_options)
                self.stream_key = stream_key
            if self.gate.last_stamp is not None and stamp <= self.gate.last_stamp:
                rospy.logwarn_throttle(2., 'Dropping duplicate/out-of-order image')
                return
            image = self.bridge.imgmsg_to_cv2(message, 'bgr8')
            start = time.perf_counter()
            detections = self.backend.predict(image)
            elapsed = (time.perf_counter()-start)*1000.
            # A fresh input may become stale while inference is running.
            age = rospy.Time.now().to_sec()-stamp
            if age > self.max_age or age < -0.05:
                rospy.logwarn_throttle(2., 'Inference result expired; increase compute capacity or reduce input size')
                return
            rows = self.gate.update(detections, stamp, image.shape[1], image.shape[0])
            result = SurfaceCandidateArray()
            result.header = message.header
            result.image_width, result.image_height = image.shape[1], image.shape[0]
            result.inference_ms = elapsed
            for row in rows:
                d = row['detection']
                item = SurfaceCandidate()
                for name in ('track_id', 'mean_confidence', 'consecutive_hits', 'stable'):
                    setattr(item, name, row[name])
                item.confidence, item.bbox_xyxy = d.confidence, list(d.box)
                item.polygon = [Point32(x=x, y=y, z=0.) for x, y in d.polygon]
                result.candidates.append(item)
            self.pub.publish(result)
            if self.debug.get_num_connections():
                overlay = image.copy()
                for row in rows:
                    d = row['detection']
                    x1, y1, x2, y2 = map(int, d.box)
                    color = (0, 200, 0) if row['stable'] else (0, 165, 255)
                    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
                    if d.polygon:
                        for a, b in zip(d.polygon, d.polygon[1:]+d.polygon[:1]):
                            cv2.line(overlay, tuple(map(int, a)), tuple(map(int, b)), color, 1)
                    text = '{} {} {:.2f} {}'.format(row['track_id'], d.label, d.confidence,
                                                    'stable' if row['stable'] else 'pending')
                    cv2.putText(overlay, text, (x1, max(16, y1-5)), cv2.FONT_HERSHEY_SIMPLEX, .5, color, 1)
                debug = self.bridge.cv2_to_imgmsg(overlay, 'bgr8')
                debug.header = message.header
                self.debug.publish(debug)
        except Exception as exc:
            # Inference errors are not published as negative/no-glass observations.
            rospy.logerr_throttle(2., 'Surface inference failed: %s', str(exc))


if __name__ == '__main__':
    rospy.init_node('surface_detector')
    try:
        node = SurfaceDetector()
    except Exception as exc:
        rospy.logfatal('Cannot start surface detector: %s', str(exc))
        raise SystemExit(1)
    rospy.spin()
