import subprocess
import sys

from common_config import *

print("1. 提取视频帧\n2. 视频帧创建蒙版\n3. 裁切图像\n4. 反推提示词\n5. 批量图生图\n6. 与帧图像融合\n7. 生成视频")
choice = input("请选择要进行的重绘工作流步骤：")

it_mode = INTERACTIVE_MODE_AUTO
if len(sys.argv) > 1:
    if 1 == int(sys.argv[1]):
        it_mode = INTERACTIVE_MODE_INPUT

config_path = input("输入配置路径：")

if choice == '1':
    # 提取视频帧
    print("开始提取视频帧：")
    subprocess.run(['python', '01_VideoFrameExtraction.py', config_path, it_mode])
if choice == '2':
    # 运行视频帧创建蒙版
    print("开始视频帧创建蒙版：")
    subprocess.run(['python', '02_MaskCreation.py', config_path, it_mode])
elif choice == '3':
    # 运行裁切图像
    print("开始裁切图像：")
    subprocess.run(['python', '03_CropImage.py', config_path, it_mode])
elif choice == '4':
    # 运行反推提示词
    print("开始反推提示词，需要SD启用API后启动，且安装WD14 Tagger插件：")
    subprocess.run(['python', '04_GeneratePrompt.py', config_path, it_mode])
elif choice == '5':
    # 运行批量图生图
    print("开始批量图生图，需要SD启用API后启动，精细化配置请打开文件修改代码：")
    subprocess.run(['python', '05_BatchImg2Img.py', config_path, it_mode])
elif choice == '6':
    # 运行图像融合
    print("开始与帧图像融合：")
    subprocess.run(['python', '06_OverlayImage.py', config_path, it_mode])
elif choice == '7':
    # 运行生成视频
    print("开始生成视频：")
    subprocess.run(['python', '07_Img2Video.py', config_path, it_mode])
else:
    print("选择了不存在的步骤……")
