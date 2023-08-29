import subprocess
import os
import torch
import shutil
import cv2
import numpy as np
from PIL import Image

print("检测是否有可用的CUDA设备中……")
# 检查是否有可用的CUDA设备
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("加速成功！使用的设备：CUDA")
else:
    device = torch.device("cpu")
    print("加速失败！使用的设备：CPU")
# 检查cuda的使用接口


# 定义寻找最大区域函数
def max_area(img):
    # 使用OpenCV 4.x版本的返回值
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # 使用list()创建一个空列表
    area = list()
    # 使用enumerate()遍历轮廓列表，并同时获取索引和元素
    for i, c in enumerate(contours):
        # 保存计算结果在一个变量中，并复用这个变量
        area_i = cv2.contourArea(c)
        area.append(area_i)
    # 同时获取最大面积的索引和值
    max_idx, max_area = max(enumerate(area), key=lambda x: x[1])

    # 遍历轮廓列表
    for k, c in enumerate(contours):
        # 跳过最大面积的轮廓
        if k == max_idx: continue
        # 绘制非最大面积的轮廓为黑色，并填充其内部区域
        cv2.drawContours(img, contours, k, 0, -1)
    return img

print("\n请选择蒙版生成算法")
print("1. 快速，速度快但质量稍差")
print("2. 标准，质量更好")

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

# 选择蒙版生成模式
choice2 = input("请输入蒙版算法的编号：")
if choice2 == '1':
    print("你选择了快速模式")
    print("开始生成蒙版，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
    subprocess.call(
        ['transparent-background', '--source', frame_out_dir, '--dest', mask_out_dir, '--type', 'map', '--fast'])
else:
    print("你选择了标准模式")
    print("开始生成蒙版，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
    subprocess.call(['transparent-background', '--source', frame_out_dir, '--dest', mask_out_dir, '--type', 'map'])

# 开始修正蒙版名称
files = sorted(os.listdir(mask_out_dir))

# 遍历文件列表  
for filename in files:  
    if filename.lower().endswith('.png'):  
        file_name, n1 = map(str, filename.split('_'))  
        new_file = f'{file_name}.png'  
  
        # 构建文件完整路径  
        file_path = os.path.join(mask_out_dir, filename)  
        new_file_path = os.path.join(mask_out_dir, new_file)  
  
        # 重命名文件  
        os.rename(file_path, new_file_path)  
        im = cv2.imread(new_file_path)  
        gray_image = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)  
        # 二值化  
        _, im_g = cv2.threshold(gray_image, 177, 255, cv2.THRESH_BINARY)  
        # 将二值化后的图像转换为numpy数组  
        im_np = np.array(im_g)  
        # 调用max_area函数，获取最大面积的图像  
        im = np.zeros_like(im_np)  # 创建与输入图像大小相同的黑色图像  
        max_area_mask = max_area(im_np)  # 获取仅包含最大轮廓的掩膜图像  
        im[max_area_mask == 255] = 255  # 将输出图像中对应的像素设为白色  
        # 将最大面积的图像写入新的文件  
        cv2.imwrite(new_file_path, im)  


print("蒙版文件生成完成！")

# 是否进行下一步
choice = input("\n是否直接开始下一步，把视频帧和蒙版进行裁切？\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '03_CropImage.py'])
else:
    quit()
