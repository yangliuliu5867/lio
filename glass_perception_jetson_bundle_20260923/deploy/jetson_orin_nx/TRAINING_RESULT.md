# Model provenance

- Model: YOLOv8n, one class `suspect_surface`
- Training dataset conversion: 2,850 train+validation images, 949 preserved test images
- Test set: 949 images, 6,790 boxes
- Test results at 640 pixels: Precision 0.883, Recall 0.704, mAP50 0.788, mAP50-95 0.544

These are public-dataset results. The threshold and temporal gate must be tuned
on recorded real camera/LiDAR sequences before use in flight experiments.
