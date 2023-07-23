import os
from PIL import Image

# 获取当前文件夹路径
folder_path = os.path.dirname(os.getcwd())
frame_path = os.path.join(folder_path, "video_frame")  #定义原始图像文件夹

# 坐标文件路径
info_file_path1 = os.path.join(folder_path,"bin","原始坐标.txt")
info_file_path2 = os.path.join(folder_path,"bin","改造坐标.txt")

# 检查坐标文件是否存在
if not os.path.isfile(info_file_path1) and not os.path.isfile(info_file_path2):
    print("覆盖信息文件均不存在！请检查后重试！")
    quit()

# 确定裁切方式
with open('原始坐标.txt', 'r') as f:
    lines = f.readlines()
    last_line = lines[-1].strip()
    if last_line.startswith('Choose me'):
        map_file="原始坐标.txt"
    else:
        map_file="改造坐标.txt"
info_file_path=os.path.join(folder_path,"bin",map_file)

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
    frame = Image.open(os.path.join(frame_path, frame)).convert("RGBA")
    filename, left, top, right, bottom = map(str, line.split(','))
    overlay = Image.open(os.path.join(overlay_folder_path, frame_w)).convert("RGBA")
    frame.paste(overlay, (int(left), int(top)), mask=overlay)
    frame.save(os.path.join(output_folder_path, frame_w))
    print(frame_w+"融合完成！")

print("所有新图已融入原图，第三步完成！")