# Orin NX deployment 2026-09-24
Workspace: /home/flag/glass_perception_jetson_bundle_20260923
Environment: yopo, Python 3.8, NVIDIA torch 2.1.0a0, TensorRT 8.5.2.2.
Installed ultralytics 8.3.40, onnx 1.16.2; pinned empy 3.3.4 and numpy 1.23.5.
The launch script preloads system libffi.so.7 for cv_bridge compatibility with Conda.

Start (close Cheese or other camera consumers first):

    bash ~/glass_perception_jetson_bundle_20260923/deploy/jetson_orin_nx/start_usb.sh

This starts ROS master if needed, USB /dev/video0 at 640x480 YUYV 30 fps,
and TensorRT detection at the configured 10 Hz timer frequency.
Stop a foreground launch with Ctrl+C. No boot service installed.

Outputs: /surface_detector/candidates and /surface_detector/debug_image.
View on NX desktop after sourcing ROS:

    rosrun rqt_image_view rqt_image_view /surface_detector/debug_image

Camera calibration is not provided. CameraInfo defaults must not be used for
metric LiDAR projection. Camera-LiDAR synchronization, extrinsic calibration,
and 3D fusion remain future work.
