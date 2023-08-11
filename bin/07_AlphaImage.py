import os
import shutil
import subprocess
from PIL import Image

# 定义工作目录
folder_path = os.path.dirname(os.getcwd())

# 定义各个参数文件夹
frame_path = os.path.join(folder_path, "video_remake")  # 重绘文件夹
mask_path = os.path.join(frame_path, "mask")    # 蒙版目录
alpha_path = os.path.join(frame_path, "alpha")  # 透明文件夹

# 透明目录存在就删除
if os.path.exists(alpha_path):
    shutil.rmtree(alpha_path)
# 创建透明输出目录
os.makedirs(alpha_path)

# 轮询开始透明
for image, mask in zip(os.listdir(frame_path), os.listdir(mask_path)):
    image_file = os.path.join(frame_path, image)
    mask_file = os.path.join(mask_path, mask)
    image_out_file = os.path.join(alpha_path, image)

    # 打开图片和蒙版
    with Image.open(image_file) as image, Image.open(mask_file).convert("L") as mask:
        # 转换成透明通道图片
        image = image.convert("RGBA")

        # 创建一个新的图像
        composited_image = Image.alpha_composite(image, Image.new("RGBA", image.size))

        # 对它应用蒙版
        composited_image.putalpha(mask)

        # 保存透明图片
        composited_image.save(image_out_file, "PNG")

    print(image_out_file + "的透明版本已生成")

# 是否进行下一步
choice = input("\n是否直接开始下一步，将调整过尺寸的图像再次生成蒙版和透明背景？\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '08_OverlayImage.py'])
else:
    quit()