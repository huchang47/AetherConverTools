import os
import shutil
from PIL import Image

# 定义工作路径
folder_path = os.path.dirname(os.getcwd())
# 定义输出图片和蒙版的目录
frame_path = os.path.join(folder_path, "video_remake")  # 图片目录
mask_path = os.path.join(frame_path, "mask")  # 蒙版目录
alpha_path = os.path.join(frame_path, "alpha")  # 输出目录

# 透明目录存在就删除
if os.path.exists(alpha_path):
    shutil.rmtree(alpha_path)
# 创建透明输出目录
os.makedirs(alpha_path)

for image, mask in zip(os.listdir(frame_path), os.listdir(mask_path)):
    image_file = os.path.join(frame_path, image)
    mask_file = os.path.join(mask_path, mask)
    image_out_file = os.path.join(alpha_path, image)

    # 打开两个文件
    with Image.open(image_file) as image2, Image.open(mask_file).convert("L") as mask:
        # 应用蒙版
        image2.putalpha(mask)
        # 保存图片
        image2.save(image_out_file, "PNG")
    print(image_out_file + "的透明版本已生成")


    