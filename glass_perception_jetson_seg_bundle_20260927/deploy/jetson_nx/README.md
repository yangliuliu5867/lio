# Jetson NX segmentation deployment

The deployment bundle contains the trained instance-segmentation checkpoint at
`models/suspect_surface_yolov8n_seg.pt`. It outputs a `suspect_surface` mask;
this is a visual candidate, not physical glass confirmation or traversability.

## One-time setup on the Jetson NX

The deployed machine is expected to use ROS Noetic and the existing `yopo`
Conda environment. TensorRT engines are tied to the GPU and JetPack/TensorRT
versions, so always build the engine on the Orin itself:

```bash
cd ~/lio/glass_perception_jetson_seg_bundle_20260927
source ~/anaconda3/etc/profile.d/conda.sh
conda activate yopo
source /opt/ros/noetic/setup.bash

catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo
chmod +x deploy/jetson_nx/*.sh
./deploy/jetson_nx/build_trt_fp16.sh
```

The build script verifies that the checkpoint task is `segment` and creates
`models/suspect_surface_yolov8n_seg.engine`.

## One-command operation

Close Cheese or any other process using the camera, then run:

```bash
bash ~/lio/glass_perception_jetson_seg_bundle_20260927/deploy/jetson_nx/start_usb.sh
```

The command starts the USB camera, TensorRT segmentation, debug overlay, and an
MJPG video recorder. Each launch gets a timestamped file under `recordings/`.
Set `show_image:=false` for a headless launch:

```bash
bash ~/lio/glass_perception_jetson_seg_bundle_20260927/deploy/jetson_nx/start_usb.sh show_image:=false
```

To record a ROS bag as well as the annotated AVI:

```bash
bash ~/lio/glass_perception_jetson_seg_bundle_20260927/deploy/jetson_nx/start_usb.sh record_bag:=true
```

Disable either recorder when storage is limited:

```bash
bash ~/lio/glass_perception_jetson_seg_bundle_20260927/deploy/jetson_nx/start_usb.sh record_video:=false record_bag:=false
```

Outputs are `/surface_detector/candidates` and
`/surface_detector/debug_image`. A segmentation result has a nonempty
`polygon` field in each candidate. Monitor with:

```bash
rostopic hz /surface_detector/candidates
rostopic echo -n 1 /surface_detector/candidates
tegrastats
```

Override paths without editing the script when another user or environment is
used:

```bash
GLASS_CONDA_ENV=yopo \
GLASS_WEIGHTS="$PWD/models/suspect_surface_yolov8n_seg.engine" \
bash deploy/jetson_nx/start_usb.sh
```

Camera calibration is not bundled. Do not use default `CameraInfo` values for
metric camera-LiDAR projection; calibrate intrinsics, extrinsics, and timing on
the installed sensors first.
