# Segmentation model provenance

- Model: YOLOv8n-seg, one class `suspect_surface`
- Checkpoint: `models/suspect_surface_yolov8n_seg.pt`
- Training dataset conversion: 2,850 train+validation images, 949 preserved test images
- Converted labels: 19,793 train+validation contours and 6,771 test contours
- Epoch 100 box metrics: Precision 0.884, Recall 0.707, mAP50 0.788, mAP50-95 0.551
- Epoch 100 mask metrics: Precision 0.870, Recall 0.684, mAP50 0.752, mAP50-95 0.478

These are public-dataset results. The threshold and temporal gate must be tuned
on recorded real camera/LiDAR sequences before use in flight experiments.
The source masks are semantic: disconnected contours approximate instances, while
touching transparent surfaces can remain a single training instance.
