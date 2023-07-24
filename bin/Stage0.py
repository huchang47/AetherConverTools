import sys
import subprocess
import os
import shutil
import time
# 获取命令行参数
args = sys.argv

# 打印命令行参数
print("命令行参数：")
for arg in args:
    print(arg)

# 定义需要处理的视频文件路径
folder_path = os.getcwd()
video_file = sys.argv[1]

# 定义帧率（这里设置为每秒截取15帧）
fps = sys.argv[2]

# 定义输出图片目录
frame_out_dir = sys.argv[3]


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

# 使用 ffmpeg 命令行工具截取视频帧，并将其保存为图片
subprocess.call([  
    "ffmpeg", "-i", video_file, 
    "-vf", "fps=" + str(fps), 
    os.path.join(frame_out_dir, "%05d.png")
])

print("\n\n视频转帧步骤已完成！码率为： "+str(fps))

# 生成蒙版
if sys.argv[4] == "True":
    # 定义蒙版目录
    mask_out_dir = sys.argv[6]

    # 蒙版目录存在就删除
    if os.path.exists(mask_out_dir):
        shutil.rmtree(mask_out_dir)
    # 创建蒙版输出目录
    os.makedirs(mask_out_dir)

    if sys.argv[5] == "True":
        print("你选择了快速模式")
        print("开始生成蒙版，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
        subprocess.run(['transparent-background','--source',frame_out_dir,'--dest',mask_out_dir,'--type','map','--fast'])
    else:
        print("你选择了标准模式")
        print("开始生成蒙版，请注意查看进度。根据图片数量，时间可能很长。\n你可以随时按Ctrl+C停止生成。")
        subprocess.run(['transparent-background','--source',frame_out_dir,'--dest',mask_out_dir,'--type','map'])
else:
    print("视频帧生成完成！")
    print("5秒后该窗口自动关闭")
    time.sleep(5)
    quit()

# 开始修正蒙版名称
files = sorted(os.listdir(mask_out_dir))

# 遍历文件列表
for filename in files:
    if filename.lower().endswith('.png'):
        file_name,n1 = map(str, filename.split('_'))
        new_file = f'{file_name}.png'

        # 构建文件完整路径
        file_path = os.path.join(mask_out_dir, filename)
        new_file_path = os.path.join(mask_out_dir, new_file)

        # 重命名文件
        os.rename(file_path, new_file_path)

print("视频帧和对应的蒙版文件生成完成！")
print("5秒后该窗口自动关闭")
time.sleep(5)