import os
import subprocess
import torch
import shutil
from PIL import Image

# 定义工作路径
folder_path = os.path.dirname(os.getcwd())
# 定义输出图片和蒙版的目录
frame_path = os.path.join(folder_path, "video_remake")
original_path = os.path.join(folder_path, "video_frame_w")
alpha_path = os.path.join(frame_path, "alpha")
upscale_path = os.path.join(frame_path, "upscale")

print("检测是否有可用的CUDA设备中……")
# 检查是否有可用的CUDA设备
if torch.cuda.is_available():
    device = 'cuda'
    print("加速成功！使用的设备：CUDA")
else:
    device = 'cpu'
    print("加速失败！使用的设备：CPU")

# 设置Torch不使用图形界面显示
os.environ["PYTORCH_JIT"] = "1"

# 使用CUDA进行加速
torch.set_grad_enabled(False)


# 定义缩放图像大小函数
def image_resize(frame_path, original_path, upscale_path):
    # 读取新图和原图的列表
    frame_files = [f for f in os.listdir(frame_path) if f.endswith('.png')]
    original_files = [f for f in os.listdir(original_path) if f.endswith('.png')]

    # 没有图的判断
    if len(frame_files) == 0:
        print(f"{frame_path}目录没有图，请检查后重试")
        quit()
    if len(original_files) == 0:
        print(f"{original_path}目录没有图，请检查后重试")
        quit()

    # 放大目录存在就删除
    if os.path.exists(upscale_path):
        shutil.rmtree(upscale_path)
    # 创建放大输出目录
    os.makedirs(upscale_path)

    for frame_file, original_file in zip(frame_files, original_files):
        frame = Image.open(os.path.join(frame_path, frame_file))
        original = Image.open(os.path.join(original_path, original_file))
        # width, height = original.size
        new_frame = frame.resize(original.size)
        new_frame.save(os.path.join(upscale_path, frame_file))
        print(f"{frame_file}的尺寸已重构为{original.size}")

# 开始进行图像尺寸调整
image_resize(frame_path, original_path, upscale_path)

# 是否进行下一步
choice = input("\n是否直接开始下一步，将调整过尺寸的图像生成透明背景图像？\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '07_AlphaImage.py'])
else:
    quit()