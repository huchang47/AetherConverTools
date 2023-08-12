import subprocess

print("2. 视频帧创建蒙版\n3. 裁切图像\n4. 反推提示词\n5. 批量图生图\n6. 调整图像尺寸\n7. 透明背景图像\n8. 与帧图像融合\n9. 生成视频")
choice = input("请选择要进行的重绘工作流步骤：")

if choice == '2':
    # 运行视频帧创建蒙版
    print("开始视频帧创建蒙版：")
    subprocess.run(['python', '02_MaskCreation.py'])
elif choice == '3':
    # 运行裁切图像
    print("开始裁切图像：")
    subprocess.run(['python', '03_CropImage.py'])
elif choice == '4':
    # 运行反推提示词
    print("开始反推提示词，需要SD启用API后启动，且安装WD14 Tagger插件：")
    subprocess.run(['python', '04_GeneratePrompt.py'])
elif choice == '5':
    # 运行批量图生图
    print("开始批量图生图，需要SD启用API后启动，精细化配置请打开文件修改代码：")
    subprocess.run(['python', '05_BatchImg2Img.py'])
elif choice == '6':
    # 运行调整图像尺寸
    print("开始调整图像尺寸：")
    subprocess.run(['python', '06_ResizeImage.py'])
elif choice == '7':
    # 运行透明背景
    print("开始生成透明背景图像：")
    subprocess.run(['python', '07_AlphaImage.py'])
elif choice == '8':
    # 运行图像融合
    print("开始与帧图像融合：")
    subprocess.run(['python', '08_OverlayImage.py'])
elif choice == '9':
    # 运行生成视频
    print("开始生成视频：")
    subprocess.run(['python', '09_Img2Video.py'])
else:
    print("选择了不存在的步骤……")