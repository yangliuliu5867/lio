# Jetson Orin NX deployment

Included model:
- `models/suspect_surface_yolov8n.pt`: training checkpoint for the ROS node.
- `models/suspect_surface_yolov8n.onnx`: fixed 640x640 portable export.

The model produces visual suspect-surface boxes. It does not itself confirm glass;
combine its boxes with synchronized LiDAR projection, point-density/return checks,
and camera-LiDAR extrinsic calibration.

## On the Orin NX

Check JetPack and TensorRT:

```bash
cat /etc/nv_tegra_release
trtexec --version
```

Use the Jetson-specific PyTorch build matching the installed JetPack, then install
Ultralytics in that environment. Build the engine on the NX itself:

```bash
chmod +x deploy/jetson_orin_nx/build_trt_fp16.sh
./deploy/jetson_orin_nx/build_trt_fp16.sh
```

This creates `models/suspect_surface_yolov8n.engine`. Do not copy an engine built
on an x86 RTX GPU: TensorRT engines bind to the GPU architecture and TensorRT /
JetPack version.

## ROS Noetic launch

```bash
source /opt/ros/noetic/setup.bash
catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo
source devel/setup.bash
roslaunch glass_perception monocular.launch \
  weights:="$(pwd)/models/suspect_surface_yolov8n.engine" \
  image_topic:=/camera/color/image_raw device:=0
```

For the first deployment, use FP16. INT8 needs representative real-camera
calibration images and a recall regression test before it can be used safely.
Test first using recorded camera/LiDAR data. Measure camera-timestamp-to-candidate
latency and observe load with `tegrastats`.
