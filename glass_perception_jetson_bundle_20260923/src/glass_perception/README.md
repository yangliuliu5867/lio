# 单目疑似表面候选框：V1

目的：在图像中找出可能对应 LiDAR 异常回波的表面区域，输出方框，供下一阶段
三维匹配使用。模型仅一个前景类别 `suspect_surface`，不是玻璃/镜子分类器。
透明玻璃、镜面及其他反光表面可统一作为候选。RGB 外观无法覆盖所有影响雷达的
因素；此输出不是“已经确认的雷达异常”，更不是可通行性或接触确认结果。

当前完成的是代码与接口，没有训练权重、真实推理结果或实机精度指标。
不订阅 LIO、不改变地图、不发布飞行命令。独立工作空间位于 lio/glass_perception_ws。

## 模块

- `scripts/surface_detector_node.py`：ROS 最新帧缓存、推理、消息和叠加图。
- `src/glass_perception/backend.py`：Ultralytics detect/segment 模型接口。
- `src/glass_perception/core.py`：像素几何检查、IoU 关联、连续帧证据过滤。
- `scripts/train_surfaces.py`：单类训练入口，支持 YOLO 检测或分割初始化权重。
- `config/dataset.example.yaml`：训练数据目录与类别模板。
- `DATASETS.md`：数据集来源、获取状态与标注注意事项。

输出 `/surface_detector/candidates` 为 `SurfaceCandidateArray`，包含原图时间戳、
frame_id、图像大小和候选框。每个框有 track_id、当前置信度、窗口平均置信度、
连续命中数和 stable。像素原点左上，x 向右、y 向下，框为 x1,y1,x2,y2；
segment 权重还输出原图像素轮廓，detect 权重轮廓为空。
`/surface_detector/debug_image` 是叠加可视化（有订阅者时发布）。

stable 仅表示连续视觉证据达到配置门槛。仍输出 pending 候选，便于下一阶段
选择召回率/稳定性策略。不会用前一帧框伪造当前帧观测。空检测发布空数组；
推理失败/过期不发布，消费者必须检查 header.stamp，不能无限沿用最后结果。

## Linux ROS Noetic 构建与启动

在 `lio/glass_perception_ws` 中执行：

```bash
source /opt/ros/noetic/setup.bash
catkin_make -DCMAKE_BUILD_TYPE=RelWithDebInfo
source devel/setup.bash
```

运行推理的 Python 必须能同时 import rospy、cv_bridge 和 ultralytics。
`requirements-noetic.txt` 给出待目标机器验证的 Python 3.8 基线，PyTorch/CUDA
按实际机器安装；不要在已有飞控环境直接升级全局依赖。训练可以在独立 GPU 环境。
得到训练权重后（下面为需要替换的示例路径）：

```bash
roslaunch glass_perception monocular.launch weights:=/path/to/best.pt image_topic:=/camera/color/image_raw device:=0
rosrun rqt_image_view rqt_image_view /surface_detector/debug_image
```

CPU 使用 `device:=cpu`。没有对应权重时启动会明确失败，不会自动下载普通 COCO
模型假装能检测此类别。若已有材料多类模型，可在 YAML 设置
`target_labels: [glass, mirror]`，统一折叠为候选框而不输出材料分类；所有指定标签
必须真实存在于权重中。

## 训练

本阶段建议先训练单类 YOLO 检测框。分割可以后续作为定位轮廓的输入，但不要求
这一版先完成实例分割。下载数据后，需把掩膜转换为框并人工审核，当前未提供或
声称完成针对所有数据集格式的转换。语义掩膜的一个连通区域不一定等于一个物体。

目录：`images/{train,val,test}`、`labels/{train,val,test}`。检测标签每行：
`0 center_x center_y width height`，坐标归一化到 [0,1]。分割模型则使用 YOLO
多边形格式，不能把检测标签用于分割训练。负样本为空标签文件，但必须确认没有
漏标的疑似表面。把 dataset.example.yaml 的 path 改为真实数据目录。

```bash
python3 src/glass_perception/scripts/train_surfaces.py --data /path/to/data.yaml --model /path/to/yolov8n.pt --device 0
```

普通预训练权重只作为训练初始化；训练后的单类 best.pt 才用于检测节点。
按场景/视频分组划分 train/val/test，公开测试集不参与训练。检查跨数据集重复图。
重点评价候选框召回率、误检/图、定位 IoU、处理延迟，以及连续视频上的框闪烁。
相邻视频帧不能随机分散到训练和测试集。

## 参数

| 参数 | 默认值 | 含义 |
|---|---:|---|
| rate_hz | 10 | 最新帧处理定时器频率，非保证推理帧率 |
| max_image_age_s | 0.5 | 输入和推理结束均检查时效 |
| inference.confidence | 0.25 | YOLO 初筛阈值 |
| inference.nms_iou | 0.5 | 类别无关 NMS 阈值 |
| inference.imgsz | 640 | 模型输入尺度，输出恢复原图坐标 |
| inference.max_det | 50 | 每帧最大框数 |
| temporal.min_hits | 3 | 连续处理帧命中数 |
| temporal.window | 5 | 有限历史窗口；漏检帧计零置信度 |
| temporal.min_mean_confidence | 0.4 | 平均置信度稳定门槛 |
| temporal.match_iou | 0.3 | 跨帧关联最小 IoU |
| temporal.ttl | 0.5 s | 距上次命中的最长保留时间 |

这些是待调试初值。时序证据不是校准后的概率；快速相机运动会造成 ID 变化，
持续误检也可能稳定。此版没有相机运动补偿。

## 方法出处与创新边界

参考 Chen et al. [Active Contact Engagement](https://arxiv.org/html/2505.00332v2)
III-A/B 的“视觉候选供后续验证”思路；该工作采用 YOLOv8 分割和 RGBD 几何。
本代码独立编写，仅完成单目单类候选与时序证据，没有复制该论文的三维维护算法。
IoU 关联与时间过滤属于常规工程，不能包装成已证实的学术创新。
项目可研究的差异在后续“视觉候选 + 实际 LiDAR 回波一致性”的验证，需消融实验，
本阶段不预先宣称实现或创新性。

Ultralytics 使用与分发应遵循其自身许可，不因本包许可而改变。
API 参考：https://docs.ultralytics.com/modes/predict/ 和 https://docs.ultralytics.com/modes/train/。

## 本地测试

```bash
python3 -m unittest discover -s src/glass_perception/test -v
```

此命令不需要 ROS/GPU/权重，只验证消息之前的候选处理逻辑。
ROS 编译和真实模型推理须在具备依赖和权重的目标主机完成，见工作空间验证记录。
