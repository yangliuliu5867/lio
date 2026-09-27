# Monocular suspect-surface ROI V1 — ExecPlan

## Purpose and current scope
User requests a new module under lio, not material classification. Single-label
YOLO bounding-box candidates for later 3-D LiDAR matching. Only M1 code/interface
milestone; no LIO modifications, point-cloud integration, map edits or flight commands.
User has no trained weights, only simulation artifacts. No inference accuracy claimed.

## Existing implementation map
Existing aerobatic_coll mujoco_ros_bridge glass_yolo_handoff_node.py has Ultralytics
inference plus simulation geometry. Kept intact. lio Point-LIO publishes
/cloud_registered and /aft_mapped_to_init; ROG-Map consumes them. Neither is a caller
of M1. New package scripts/surface_detector_node.py uses backend.YoloBackend and
core.TemporalGate, emits SurfaceCandidateArray and debug Image. train_surfaces.py
provides the independent single-class training entry.

## Reference/method map
Chen et al. https://arxiv.org/html/2505.00332v2 III-A/B: YOLOv8 segmentation,
RGBD boundary geometry and incremental 3-D surface maintenance. Reference concept
only, not reproduction or copied source. No paper equations implemented.
IoU association and rolling evidence are conventional engineering; no novelty claim.
Potential future contribution: visually proposed regions checked against measured
LiDAR return inconsistencies. Outside this milestone; needs literature/ablation.

## Milestones
M1: ROS package, YOLO adapter, ROI messages, pure temporal tests, training entry,
source dataset inventory. Code implemented; pure checks pass; ROS build/inference
remain unverified due to unavailable environment and trained weights.
M2: acquire/audit/convert datasets and train weights. Not started.
M3: image-to-LIO geometry matching. Not started.

## Data/frame and variables
Original-image pixels x-right/y-down; source header retained. No depth/normal claim.
One class suspect_surface. Confidence-weighted class voting was removed following
user clarification. Current evidence: greedy one-to-one IoU matching, current-box
output, consecutive hit count, rolling mean confidence including missed frames as
zero. Missing tracks never emitted; timestamp/order/expiry checks enforced.
No optimization variables or gradients. Threshold ranges validated in core/backend.

## Compatibility and parameters
Independent lio/glass_perception_ws/src/glass_perception package. Existing launches
unchanged. Config includes image age/rate, model confidence/NMS/size/device/max boxes,
target labels, temporal hits/window/mean confidence/IoU/TTL. README documents defaults.
Known multi-class weights may explicitly map several labels to one candidate type;
generic COCO weights without requested labels fail. One-class training schema.

## Acceptance and exact verification commands
Run from package parent workspace after migration:
- python3 -m unittest discover -s src/glass_perception/test -v
  Executed in initial staging workspace: exit 0, 17 tests passed.
- python3 src/glass_perception/tools/validate_sources.py
  Checks Python 3.8 AST and package/launch XML; result recorded in VALIDATION.md.
Tests cover weak persistent detections, misses/expiry, no ghost outputs, one-to-one
association, timestamps, invalid pixels/config, label mapping and missing weights.
ROS acceptance pending: source /opt/ros/noetic/setup.bash; catkin_make;
catkin_make run_tests; catkin_test_results --verbose (not executed on this Mac).
Actual YOLO validation requires compatible Torch/Ultralytics and trained weights.

## Decisions, evidence and risks
2026-09-22: user corrected initial glass/mirror classification concept to one ROI type.
Dataset search found 3DRef RGB/all-reflective masks as primary aligned-domain source,
GSD and Trans10K as supplements. No dataset downloaded or label conversion claimed.
Licenses/access boundaries in DATASETS.md. Do not confuse website license with data.
Current Mac: Python 3.14.7; no cv2/numpy/yaml/catkin_pkg/torch/ultralytics in default
Python, no ROS Noetic/catkin_make. Pure checks do not establish real inference/build.
Fast image motion loses IoU identity; stable false positives remain possible. RGB
cannot cover every sensor failure cause. Training domain mismatch and incomplete
cross-dataset annotations require audit. No synthetic performance evidence.

## Rollback
Remove only new glass_perception_ws. No changes to existing LIO, ROG-Map or control.
