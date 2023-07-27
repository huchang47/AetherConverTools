import os
import torch
import numpy as np
import shutil
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

# 生成坐标文件
width = int(width)
height = int(height)

# 步骤一：创建备用1.txt文件，进行第一轮转换
print("正在执行步骤一：新建备用1.txt文件...")

if os.path.exists("备用1.txt"):
    os.remove("备用1.txt")
with open("备用1.txt", "w") as f:
    pass

# 步骤二：计算坐标差值和平均值，并将结果写入备用1.txt
print("正在执行步骤二：计算坐标差值和平均值...")
with open(output_file_path, "r") as f:
    lines = f.readlines()

count = 0
for line in lines:
    print("正在处理行:", line.strip())  # 输出行内容
    filename,x1,y1,x2,y2 = map(str,line.split(','))
    x1, y1, x2, y2 = int(x1),int(y1),int(x2),int(y2)

    diff_x = x2 - x1
    diff_y = y2 - y1
    avg_x = (x1 + x2) // 2
    avg_y = (y1 + y2) // 2

    with open("备用1.txt", "a") as f:
        new_line = f"{filename},{diff_x},{diff_y},{avg_x},{avg_y}\n"
        f.write(new_line)

    count += 1

print(f"已处理 {count} 行数据，并将结果写入备用1.txt。")

# 步骤三：新建备用2.txt文件
print("正在执行步骤四：新建备用2.txt文件...")

if os.path.exists("备用2.txt"):
    os.remove("备用2.txt")

with open("备用2.txt", "w") as f:
    pass

# 步骤四：借助备用1.txt的信息生成备用2.txt
print("步骤四：借助备用1.txt的信息生成备用2.txt")

max_x_diff = 0
max_y_diff = 0

with open("备用1.txt", "r") as f:
    lines = f.readlines()

for line in lines:

    filename,x1,y1,x2,y2 = map(str,line.split(','))

    x_diff = int(x1)
    y_diff = int(y1)

    if x_diff > max_x_diff:
        max_x_diff = x_diff

    if y_diff > max_y_diff:
        max_y_diff = y_diff

print("最大X坐标差值:", max_x_diff)
print("最大Y坐标差值:", max_y_diff)

piancha_x = 0
piancha_y = 0

if max_x_diff > width:
	max_x_diff = width
	piancha_x = 1
	print("尺寸过小，为了程序运行，已修正X数值")
	print("最大X坐标差值:", max_x_diff)
if max_y_diff > height:
	max_y_diff = height
	piancha_y = 1
	print("尺寸过小，为了程序运行，已修正Y数值")
	print("最大Y坐标差值:", max_y_diff)

with open("备用2.txt", "w") as f:
    for line in lines:
        filename,x1,y1,x2,y2 = map(str,line.split(','))
        x1, y1, x2, y2 = int(x1),int(y1),int(x2),int(y2)

        new_x1 = x2 - round(max_x_diff / 2, 1)
        new_y1 = y2 - round(max_y_diff / 2, 1)
        new_x2 = x2 + round(max_x_diff / 2, 1)
        new_y2 = y2 + round(max_y_diff / 2, 1)
        new_line = f"{filename},{new_x1:.1f},{new_y1:.1f},{new_x2:.1f},{new_y2:.1f}\n"
        f.write(new_line)
        
		
        print("x1值:", x1)
        print("y1值:", y1)
        print("x2值:", x2)
        print("y2值:", y2)

# 步骤五：新建坐标.txt文件
print("正在执行步骤五：新建改造坐标.txt文件...")

if os.path.exists("改造坐标.txt"):
    os.remove("改造坐标.txt")

with open("改造坐标.txt", "w") as f:
    pass

# 步骤六：借助备用2.txt的信息生成改造坐标.txt
print("步骤六：借助备用2.txt的信息生成改造改造坐标.txt...")
with open("备用2.txt", "r") as f:
    lines = f.readlines()

for line in lines:
    filename,x1,y1,x2,y2 = map(str,line.split(','))
    x1, y1, x2, y2 = float(x1),float(y1),float(x2),float(y2)

    if piancha_x == 0:
        if x1 < 0:
            p = 0 - x1
            x1 = x1 + p
            x2 = x2 + p

        if x2 > float(width):
            p = x2 - float(width)
            x2 = x2 - p
            x1 = x1 - p

    if piancha_y == 0:
        if y1 < 0:
            q = 0 - y1
            y1 = y1 + q
            y2 = y2 + q

        if y2 > float(height):
            q = y2 - float(height)
            y2 = y2 - q
            y1 = y1 - q

    with open("改造坐标.txt", "a") as f:
        filename = os.path.splitext(filename)[0]
        new_line = f"{filename},{int(x1)},{int(y1)},{int(x2)},{int(y2)}\n"
        f.write(new_line)

print("第六步完成，改造坐标.txt文件生成完毕。")

os.remove("备用1.txt")
os.remove("备用2.txt")
#os.remove(output_file_path)

print("\n\n\n请选择图像裁切方式：")
print("1. 原始坐标（按照蒙版原始大小裁切，每张图尺寸不同）")
print("2. 最大坐标（按照最大蒙版大小裁切，每张图相同尺寸）")

choice = input("请输入裁切方式的编号：")

if choice == '1':
    print("你选择了原始坐标裁切")
    map_file = "原始坐标.txt"
elif choice == '2':
    print("你选择了最大坐标裁切")
    map_file = "改造坐标.txt"
else:
    print("无效的选择，默认采用原始坐标方式裁切")
    map_file = "原始坐标.txt"

# 把选择结果存起来，第三步方便调用
with open(map_file, "a") as f:
    f.write("Choose me")

# 坐标文件路径
folder_path = os.path.dirname(os.getcwd())
info_file_path = os.path.join(folder_path,"bin",map_file)

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

print("所有帧和蒙版均裁切完毕，第一步完成！\n请进行图生图！")