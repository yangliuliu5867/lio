#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bundle_dir="$(cd "${script_dir}/../.." && pwd)"
conda_sh="${GLASS_CONDA_SH:-${HOME}/anaconda3/etc/profile.d/conda.sh}"
conda_env="${GLASS_CONDA_ENV:-yopo}"
weights="${GLASS_WEIGHTS:-${bundle_dir}/models/suspect_surface_yolov8n_seg.engine}"

[[ -f "$conda_sh" ]] || { echo "Missing Conda setup: $conda_sh" >&2; exit 2; }
[[ -f "$weights" ]] || { echo "Missing segmentation engine: $weights" >&2; exit 2; }
source "$conda_sh"
conda activate "$conda_env"
source /opt/ros/noetic/setup.bash
cd "$bundle_dir"
[[ -f devel/setup.bash ]] || { echo "Run catkin_make before starting." >&2; exit 2; }
source devel/setup.bash
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libffi.so.7${LD_PRELOAD:+:$LD_PRELOAD}
if [[ -z "${DISPLAY:-}" ]]; then
  export DISPLAY=:1
  export XAUTHORITY="${HOME}/.Xauthority"
fi
mkdir -p recordings
stamp="$(date +%Y%m%d_%H%M%S)"
video_file="$PWD/recordings/segmentation_${stamp}_$$.avi"
bag_file="$PWD/recordings/segmentation_${stamp}_$$"
echo "Detection video: $video_file"
echo "Segmentation engine: $weights"
exec roslaunch deploy/jetson_nx/usb_camera.launch \
  weights:="$weights" video_file:="$video_file" bag_file:="$bag_file" "$@"
