#!/usr/bin/env bash
# Run this on the target Jetson NX. Engine files are not portable across GPUs or JetPack releases.
set -euo pipefail
ws_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
weights="${1:-${ws_dir}/models/suspect_surface_yolov8n_seg.pt}"
imgsz="${2:-640}"
if [[ ! -f "$weights" ]]; then echo "Missing weights: $weights" >&2; exit 2; fi
if ! command -v yolo >/dev/null 2>&1; then echo "Install Jetson-compatible PyTorch and ultralytics first." >&2; exit 2; fi
python - "$weights" <<'PY'
import sys
from ultralytics import YOLO
model = YOLO(sys.argv[1])
if model.task != "segment":
    raise SystemExit("Expected a segment checkpoint, got task=%s" % model.task)
print("Verified segmentation checkpoint:", model.names)
PY
yolo export model="$weights" format=engine imgsz="$imgsz" device=0 half=True
engine="${weights%.*}.engine"
[[ -f "$engine" ]] || { echo "Expected engine was not created: $engine" >&2; exit 3; }
echo "Ready: $engine"
