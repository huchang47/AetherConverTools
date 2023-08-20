import subprocess
import os
import torch
import shutil

print("检测是否有可用的CUDA设备中……")
# 检查是否有可用的CUDA设备
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("加速成功！使用的设备：CUDA")
else:
    device = torch.device("cpu")
    print("加速失败！使用的设备：CPU")

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
    subprocess.run(
        ['transparent-background', '--source', frame_out_dir, '--dest', mask_out_dir, '--type', 'map', '--fast'])
else:
    print("你选择了标准模式")
    print("开始生成蒙版，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
    subprocess.run(['transparent-background', '--source', frame_out_dir, '--dest', mask_out_dir, '--type', 'map'])

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

print("蒙版文件生成完成！")

# 是否进行下一步
choice = input("\n是否直接开始下一步，把视频帧和蒙版进行裁切？\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '03_CropImage.py'])
else:
    quit()
