import subprocess
import os
import torch
import shutil

# 定义需要处理的视频文件路径
folder_path = os.path.dirname(os.getcwd())
video_file = os.path.join(folder_path, "video.mp4")

# 定义输出图片和蒙版的目录
frame_out_dir = os.path.join(folder_path, "video_frame")
mask_out_dir = os.path.join(folder_path, "video_mask")

# 检查是否有可用的CUDA设备
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("加速成功！使用的设备：CUDA")
else:
    device = torch.device("cpu")
    print("加速失败！使用的设备：CPU")

# 帧目录存在就删除
if os.path.exists(frame_out_dir):
    shutil.rmtree(frame_out_dir)
# 创建帧输出目录
os.makedirs(frame_out_dir)

# 定义帧率（这里设置为每秒截取15帧）
fps = input("请输入想要输出的视频帧率（默认15）：") or 15

# 设置Torch不使用图形界面显示
os.environ["PYTORCH_JIT"] = "1"

# 使用CUDA进行加速
torch.set_grad_enabled(False)

# 使用 ffmpeg 命令行工具截取视频帧，并将其保存为图片
subprocess.call([
    "ffmpeg", "-i", video_file,
    "-vf", "fps=" + str(fps),
    os.path.join(frame_out_dir, "%05d.png")
])

print("\n\n视频转帧步骤已完成！码率为： " + str(fps))

# 是否进行下一步
choice = input("\n是否直接开始下一步，将视频帧输出为蒙版？\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '02_MaskCreation.py'])
else:
    quit()
