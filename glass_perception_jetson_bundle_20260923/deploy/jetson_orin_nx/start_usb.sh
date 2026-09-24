#!/usr/bin/env bash
set -e
source /home/flag/anaconda3/etc/profile.d/conda.sh
conda activate yopo
source /opt/ros/noetic/setup.bash
cd /home/flag/glass_perception_jetson_bundle_20260923
source devel/setup.bash
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libffi.so.7${LD_PRELOAD:+:$LD_PRELOAD}
if [[ -z "${DISPLAY:-}" ]]; then
  export DISPLAY=:1
  export XAUTHORITY=/home/flag/.Xauthority
fi
mkdir -p recordings
video_file="$PWD/recordings/detection_$(date +%Y%m%d_%H%M%S)_$$.avi"
echo "Detection video: $video_file"
exec roslaunch deploy/jetson_orin_nx/usb_camera.launch video_file:="$video_file" "$@"
