# Jetson NX deployment 2026-09-24
Workspace: /home/flag/lio/glass_perception_jetson_seg_bundle_20260927
Environment: yopo, Python 3.8, NVIDIA torch 2.1.0a0, TensorRT 8.5.2.2.
Installed ultralytics 8.3.40, onnx 1.16.2; pinned empy 3.3.4 and numpy 1.23.5.
The launch script preloads system libffi.so.7 for cv_bridge compatibility with Conda.

Start (close Cheese or other camera consumers first):

    bash ~/lio/glass_perception_jetson_seg_bundle_20260927/deploy/jetson_nx/start_usb.sh

This starts ROS master if needed, USB /dev/video0 at 640x480 YUYV 30 fps,
TensorRT instance segmentation at the configured 10 Hz timer frequency, and a
timestamped annotated AVI recording. Pass `record_bag:=true` to also record the
camera, candidates, and debug image as a ROS bag.
Stop a foreground launch with Ctrl+C. No boot service installed.

Outputs: /surface_detector/candidates and /surface_detector/debug_image.
View on NX desktop after sourcing ROS:

    rosrun rqt_image_view rqt_image_view /surface_detector/debug_image

The current default engine is `models/suspect_surface_yolov8n_seg.engine`.
Successful segment output has nonempty polygon arrays in candidate messages.

Camera calibration is not provided. CameraInfo defaults must not be used for
metric LiDAR projection. Camera-LiDAR synchronization, extrinsic calibration,
and 3D fusion remain future work.
