# Pixel coordinates in the original image, NOT world geometry or contact confirmation.
uint32 track_id
float32 confidence
float32 mean_confidence
uint32 consecutive_hits
bool stable
float32[4] bbox_xyxy
# Empty for detect-only weights; current-frame segmentation boundary otherwise.
geometry_msgs/Point32[] polygon
