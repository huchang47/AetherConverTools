import os
import torch
import shutil
import subprocess
from PIL import Image

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

# 定义工作目录
folder_path = os.path.dirname(os.getcwd())

# 定义各个参数文件夹
frame_path = os.path.join(folder_path, "video_remake")  # 重绘文件夹
mask_path = os.path.join(frame_path, "mask")    # 蒙版目录
alpha_path = os.path.join(frame_path, "alpha")  # 透明文件夹
upscale_path = os.path.join(frame_path, "upscale")  # 放大文件夹

# 透明目录存在就删除
if os.path.exists(alpha_path):
    shutil.rmtree(alpha_path)
# 创建透明输出目录
os.makedirs(alpha_path)

# 定义生成透明图片函数
def image_alpha(frame_path,alpha_path):
    print("开始进行透明背景操作：")

    # 透明目录存在就删除
    if os.path.exists(alpha_path):
        shutil.rmtree(alpha_path)
    # 透明图片输出目录
    os.makedirs(alpha_path)

    print("选择透明生成算法：\n1. 快速，速度快但质量稍差\n2. 标准，质量更好")

    # 选择蒙版生成模式
    choice2 = input("请输入透明算法的编号：")
    if choice2 == '1':
        print("你选择了快速模式")
        print("开始生成透明背景图，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
        subprocess.run(['transparent-background','--source',frame_path,'--dest',alpha_path,'--type','rgba','--fast'])
    else:
        print("你选择了标准模式")
        print("开始生成透明背景图，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
        subprocess.run(['transparent-background','--source',frame_path,'--dest',alpha_path,'--type','rgba'])
    # 开始修正图像名称
    files = sorted(os.listdir(alpha_path))
    # 遍历文件列表
    for filename in files:
        if filename.lower().endswith('.png'):
            file_name,n1 = map(str, filename.split('_'))
            new_file = f'{file_name}.png'

            # 构建文件完整路径
            file_path = os.path.join(alpha_path, filename)
            new_file_path = os.path.join(alpha_path, new_file)

            # 重命名文件
            os.rename(file_path, new_file_path)
    print(f"图生图的透明背景图已生成，在{frame_path}的{alpha_path}目录内。")

image_alpha(upscale_path,alpha_path)

# 是否进行下一步
choice = input("\n是否直接开始下一步，将透明图像按照对应位置覆盖回原始图像？\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '08_OverlayImage.py'])
else:
    quit()