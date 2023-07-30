import os
import torch
import numpy as np
import shutil
import subprocess
from torchvision import transforms
from PIL import Image

# 检查是否有可用的CUDA设备
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("加速成功！使用的设备：CUDA")
else:
    device = torch.device("cpu")
    print("加速失败！使用的设备：CPU")

# 定义一个倍数函数
def multiple(num,mul):
    return (num // mul + 1) * mul

# 获取当前文件夹路径
folder_path = os.path.dirname(os.getcwd())
mask_path = os.path.join(folder_path, "video_mask")    #定义蒙版文件夹
frame_path = os.path.join(folder_path, "video_frame")  #定义原始图像文件夹

# 创建蒙版竖版文件夹
mask_out_folder = mask_path+"_w"
mask_out_folder_path = os.path.join(folder_path, mask_out_folder)
# 蒙版文件夹存在就删除
if os.path.exists(mask_out_folder_path):
    shutil.rmtree(mask_out_folder_path)
# 不存在就创建
if not os.path.exists(mask_out_folder_path):
    os.makedirs(mask_out_folder_path)

# 创建记录原始坐标的TXT文件
output_file = "原始坐标.txt"
output_file_path = os.path.join(folder_path,"bin",output_file)

# 检查是否存在原始坐标文件，如果存在则删除
if os.path.exists(output_file_path):
    os.remove(output_file_path)

# 裁切蒙版函数
def crop_mask_image(file_path, output_path):
    try:
        image = Image.open(file_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # 转换图像为Tensor并将其移动到CUDA设备上
        image_tensor = transforms.ToTensor()(image).unsqueeze(0).to(device)

        # 执行裁切操作
        mask = (torch.abs(image_tensor - 1.0) <= 0.5).all(dim=1)
        non_zero_indices = torch.nonzero(mask)
        left = non_zero_indices[:, 2].min().item()
        top = non_zero_indices[:, 1].min().item()
        right = non_zero_indices[:, 2].max().item()
        bottom = non_zero_indices[:, 1].max().item()

        # 检查裁切点是否有效
        if left >= right or top >= bottom:
            print(f"错误：{file_path} 中未找到足够的白色像素区域。")
            return
        
        # 裁切后长宽需要是8的倍数
        frame_w,frame_h=image.size  #原图长和高
        dw = right-left #差值 裁切后图的长
        dh = bottom-top #差值 裁切后图的高
        frame_w2 = multiple(dw,8)    #长重整为8的倍数
        frame_h2 = multiple(dh,8)    #高重整为8的倍数
        dw2 = frame_w2-dw   #新长和旧长的差值
        dh2 = frame_h2-dh   #新高和旧高的差值
        if left > dw2:  #如果左侧还有地方
            left = left - dw2   #差值就加到左边
        elif frame_w - right >dw2:  #如果右侧还有地方
            right = right + dw2 #差值就加到右边
        if top > dh2:   #如果上面还有地方
            top = top - dh2 #差值就加到上面
        elif frame_h - bottom > dh2:    #如果下面还有地方
            bottom = bottom + dh2   #差值就加到下面

        # 转换为NumPy数组并裁切图像
        image_array = np.array(image)
        cropped_image = Image.fromarray(image_array[top:bottom+1, left:right+1])

        # 保存裁切后的图像
        cropped_image.save(output_path)
        print(f"{file_path} 已裁切完毕。")
        print(f"裁切点：({left},{top}) , ({right},{bottom})")

        # 将原始坐标即时写入TXT文件
        info = f"{file_name[:-4]},{left},{top},{right},{bottom}\n"
        with open(output_file_path, 'a') as info_file:
            info_file.write(info)
    except Exception as e:
        print(f"错误：处理 {file_path} 时出现异常。")
        print(str(e))

# 遍历蒙版文件夹下的所有PNG图片
png_files = [f for f in os.listdir(mask_path) if f.endswith('.png')]

# 设置Torch不使用图形界面显示
os.environ["PYTORCH_JIT"] = "1"

# 使用CUDA进行加速
torch.set_grad_enabled(False)

# 遍历蒙版并处理每张图片
for file_name in png_files:
    file_path = os.path.join(mask_path, file_name)
    output_path = os.path.join(mask_out_folder_path, file_name)
    crop_mask_image(file_path, output_path)
    # 自动获取原始图像的宽度和高度
    with Image.open(file_path) as img:
        width, height = img.size
        print('图片尺寸为：{}x{}'.format(width, height))
    
print(f"原始坐标已保存至 {output_file_path}")

# 坐标文件路径
folder_path = os.path.dirname(os.getcwd())
info_file_path = os.path.join(folder_path,"bin","原始坐标.txt")

# 检查坐标文件是否存在
if not os.path.isfile(info_file_path):
    print("坐标文件不存在！")
    exit()

# 创建输出文件夹
frame_out_folder = frame_path+"_w"
frame_out_folder_path = os.path.join(folder_path, frame_out_folder)
# 输出文件夹存在就删除
if os.path.exists(frame_out_folder_path):
    shutil.rmtree(frame_out_folder_path)
# 不存在就创建
if not os.path.exists(frame_out_folder_path):
    os.makedirs(frame_out_folder_path)

# 读取坐标文件
with open(info_file_path, 'r') as info_file:
    lines = info_file.read().splitlines()

# 开始裁切视频帧
frame_files = [f for f in os.listdir(frame_path) if f.endswith('.png')]

for file, line in zip(frame_files, lines):
    if file.endswith('.png'):
        img = Image.open(os.path.join(frame_path, file))
        line = line.strip()
        filename, left, top, right, bottom = map(str, line.split(','))
        cropped_img = img.crop((int(left), int(top), int(right), int(bottom)))
        cropped_img.save(os.path.join(frame_out_folder_path, file))
        print("帧"+file+"裁切完成！")

# 重新裁切与帧大小对应的蒙版
for file, line in zip(os.listdir(mask_path), lines):
    if file.endswith('.png'):
        img = Image.open(os.path.join(mask_path, file))
        line = line.strip()
        filename, left, top, right, bottom = map(str, line.split(','))
        cropped_img = img.crop((int(left), int(top), int(right), int(bottom)))
        cropped_img.save(os.path.join(mask_out_folder_path, file))
        print("蒙版"+file+"裁切完成！")

Choice=input("\n\n\n是否开始反推提示词？\n1. 是\n2. 否\n请输入你选择的编号：")
if Choice == 1:
    subprocess.run(["python", "Stage1.5.py"])  # 执行Stage1.5.py文件

print("当前步骤操作完毕，第一步完成！\n请进行第二步图生图！")