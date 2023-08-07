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


# 定义生成透明图片函数
def image_alpha(frame_path, alpha_path):
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
        subprocess.run(
            ['transparent-background', '--device', device, '--source', frame_path, '--dest', alpha_path, '--type',
             'rgba', '--fast'])
    else:
        print("你选择了标准模式")
        print("开始生成透明背景图，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
        subprocess.run(
            ['transparent-background', '--device', device, '--source', frame_path, '--dest', alpha_path, '--type',
             'rgba'])
    # 开始修正图像名称
    files = sorted(os.listdir(alpha_path))
    # 遍历文件列表
    for filename in files:
        if filename.lower().endswith('.png'):
            file_name, n1 = map(str, filename.split('_'))
            new_file = f'{file_name}.png'

            # 构建文件完整路径
            file_path = os.path.join(alpha_path, filename)
            new_file_path = os.path.join(alpha_path, new_file)

            # 重命名文件
            os.rename(file_path, new_file_path)
    print(f"图生图的透明背景图已生成，在{frame_path}的{alpha_path}目录内。")


# 选择周边功能
print("请选择使用的周边功能")
print("1. 图生图还原大小")
print("2. 图生图透明背景")
print("3. 我全都要！")
choice = input("请输入周边功能编号：")

if choice == '1':
    image_resize(frame_path, original_path, upscale_path)

elif choice == '2':
    image_alpha(frame_path, alpha_path)

elif choice == '3':
    image_resize(frame_path, original_path, upscale_path)
    image_alpha(upscale_path, alpha_path)

else:
    print("其他的功能还在一生悬命开发中，敬请期待，或找作者催更。")
    quit()
