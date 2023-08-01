import os
from PIL import Image

# 获取当前文件夹路径
folder_path = os.path.dirname(os.getcwd())
frame_path = os.path.join(folder_path, "video_frame")  #定义原始图像文件夹
remake_path = os.path.join(folder_path, "video_remake")  #定义原始图像文件夹
alpha_path = os.path.join(folder_path,"video_remake","alpha")   # 定义透明图像文件夹

# 坐标文件路径
info_file_path = os.path.join(folder_path,"bin","原始坐标.txt")

# 选择用什么图融合
print("请选择使用怎样的图进行融合：\n1. 图生图标准图像\n2. 透明背景图像（需先执行Etc中的透明操作）")
Choice=input("你选择使用怎样的图像呢：")
if Choice == '1':
    work_path = remake_path
else:
    work_path = alpha_path

# 判断图是否存在
try:
    png_files = [file for file in os.listdir(work_path) if file.endswith('.png')]
except Exception as e:
    print(f"你还没有{work_path}这个文件夹，请检查后重试")
    quit()
if len(png_files) == 0:
    print("你选择的图像目录中没有任何PNG图片，请检查后重试")
    quit()

# 检查坐标文件是否存在
if not os.path.isfile(info_file_path):
    print("覆盖信息文件均不存在！请检查后重试！")
    quit()

# 竖版图生图文件夹路径
overlay_folder_path = os.path.join(folder_path, "video_remake")

# 创建横版输出文件夹
output_folder_path = os.path.join(folder_path, frame_path+"_Done")
if not os.path.exists(output_folder_path):
    os.makedirs(output_folder_path)

# 遍历坐标文件
with open(info_file_path, 'r') as info_file:
    lines = info_file.readlines()

# 开始遍历融合
for frame,frame_w, line in zip(os.listdir(frame_path), os.listdir(overlay_folder_path),lines):
    if frame.endswith('.png'):
        frame = Image.open(os.path.join(frame_path, frame)).convert("RGBA") # 打开原图
        filename, left, top, right, bottom = map(str, line.split(','))  # 读取坐标
        overlay = Image.open(os.path.join(work_path, frame_w)).convert("RGBA")  # 打开新图
        frame.paste(overlay, (int(left), int(top)), mask=overlay)   # 贴进去
        frame.save(os.path.join(output_folder_path, frame_w))   # 保存
        print(frame_w+"融合完成！")

print("所有新图已融入原图，第三步完成！")