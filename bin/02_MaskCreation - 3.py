import os
import shutil

import torch
from ultralytics import YOLO

print("检测是否有可用的CUDA设备中……")
# 检查是否有可用的CUDA设备
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("加速成功！使用的设备：CUDA")
else:
    device = torch.device("cpu")
    print("加速失败！使用的设备：CPU")

# 定义需要处理的视频文件路径
folder_path = os.path.dirname(os.getcwd())

# 定义输出图片和蒙版的目录
frame_out_dir = os.path.join(folder_path, "video_frame")
mask_out_dir = os.path.join(folder_path, "video_mask")

# 蒙版目录存在就删除
if os.path.exists(mask_out_dir):
    shutil.rmtree(mask_out_dir)
# 创建蒙版输出目录
os.makedirs(mask_out_dir)

# 设置Torch不使用图形界面显示
os.environ["PYTORCH_JIT"] = "1"

# 使用CUDA进行加速
torch.set_grad_enabled(False)



# Load a pretrained YOLOv8n model
model = YOLO('yolov8n.pt')

# Run inference on an image
results = model(frame_out_dir)  # list of 1 Results object
for r in results:
    print(r.keypoints)