import os
import subprocess
import shutil
from PIL import Image

# 定义工作路径
folder_path = os.path.dirname(os.getcwd())
# 定义输出图片和蒙版的目录
frame_path = os.path.join(folder_path, "video_remake")
mask_path = os.path.join(frame_path, "mask")
frame_alpha_path = os.path.join(frame_path, "alpha")

# 选择周边功能
print("请选择使用的周边功能")
print("1. 图生图蒙版")
print("2. 图生图透明背景")
choice = input("请输入周边功能编号：")

if choice == '1':
    print("开始将图生图生成蒙版：")

    # 蒙版目录存在就删除
    if os.path.exists(mask_path):
        shutil.rmtree(mask_path)
    # 创建蒙版输出目录
    os.makedirs(mask_path)

    print("生成！拆解一切，启动！")
    print("\n选择蒙版生成算法")
    print("1. 快速，速度快但质量稍差")
    print("2. 标准，质量更好")

    # 选择蒙版生成模式
    choice2 = input("请输入蒙版算法的编号：")
    if choice2 == '1':
        print("你选择了快速模式")
        print("开始生成蒙版，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
        subprocess.run(['transparent-background','--source',frame_path,'--dest',mask_path,'--type','map','--fast'])
    else:
        print("你选择了标准模式")
        print("开始生成蒙版，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
        subprocess.run(['transparent-background','--source',frame_path,'--dest',mask_path,'--type','map'])
    # 开始修正蒙版名称
    files = sorted(os.listdir(mask_path))
    # 遍历文件列表
    for filename in files:
        if filename.lower().endswith('.png'):
            file_name,n1 = map(str, filename.split('_'))
            new_file = f'{file_name}.png'

            # 构建文件完整路径
            file_path = os.path.join(mask_path, filename)
            new_file_path = os.path.join(mask_path, new_file)

            # 重命名文件
            os.rename(file_path, new_file_path)
    print("图生图的新蒙版已生成，在video_remake的mask目录下。")

elif choice == '2':
    print("开始图生图透明背景：")
    # 检查蒙版文件是否存在
    if not os.listdir(folder_path):
        print("蒙版文件不存在！")
        quit()

    # 透明目录存在就删除
    if os.path.exists(frame_alpha_path):
        shutil.rmtree(frame_alpha_path)
    # 创建透明输出目录
    os.makedirs(frame_alpha_path)
    
    for image,mask in zip(os.listdir(frame_path),os.listdir(mask_path)):
        # 打开两个文件
        if image.endswith('.png') and mask.endswith('.png'):
            image_out = os.path.join(frame_alpha_path, image)
            imagename=image
            image = Image.open(os.path.join(frame_path,image))
            mask = Image.open(os.path.join(mask_path,mask))
            # 将蒙版图片转换为透明掩码模式
            mask = mask.convert("L")
            # 将原始图片应用蒙版
            image.putalpha(mask)
            # 保存合成后的图像为PNG格式，保留透明通道
            image.save(image_out, "PNG")
            print(imagename+"的透明版本已生成")

    print("图生图的透明版本已生成，在video_remake的alpha目录下。")

else:
    print("其他的功能还在一生悬命开发中，敬请期待，或找作者催更。")
    quit()
