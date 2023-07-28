import os
import shutil
import requests
import io
import base64
import json
from io import BytesIO
from PIL import Image, PngImagePlugin

# 定义本机的SD网址
url = "http://127.0.0.1:7860"

# 定义CN模型数据接口
def ListCN():
    cn_url = url + "/controlnet/control_types"
    CN_list = requests.get(url=cn_url).json()
    return CN_list

# 定义获取本地CN数据函数
def get_CNmap():
    CN_model_map={}
    num=0
    data=ListCN()["control_types"]
    for k in data:
        if k!="All":
            CN_model_map[num]=k
            print(str(num)+". ",k)
            num+=1
    Choice1=int(input("请选择模型编号："))
    print("选择的是",CN_model_map[Choice1])
    mod_dic={} 
    num=0
    for k in data[CN_model_map[Choice1]]["module_list"]:
        mod_dic[num] = k
        print(str(num)+". ",k)
        num+=1
    Choice2=int(input("请选择预处理器编号："))
    print("选择的是：",mod_dic[Choice2])
    wei=input("请输入该ControlNet的权重：")
    Mode_name,Mod_name = mod_dic[Choice2],data[CN_model_map[Choice1]]["default_model"]
    return [Mode_name,Mod_name,wei]

# 定义输入文件夹
folder_path = os.path.dirname(os.getcwd())
mask_path = os.path.join(folder_path, "video_mask_w")    #定义蒙版文件夹
frame_path = os.path.join(folder_path, "video_frame_w")  #定义原始图像文件夹

# 定义图片转base64函数
def img_str(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# 图生图输出文件夹
out_path = os.path.join(folder_path, "video_remake")
# 蒙版文件夹存在就删除
if os.path.exists(out_path):
    shutil.rmtree(out_path)
# 不存在就创建
if not os.path.exists(out_path):
    os.makedirs(out_path)

# 轮询输入目录
frame_files = [f for f in os.listdir(frame_path) if f.endswith(".png")]
txt_files = [f for f in os.listdir(frame_path) if f.endswith(".txt")]

if len(frame_files) == 0:
    print("裁切后图片目录中没有任何图片，请检查"+frame_path+"目录后重试。")
    quit()
if len(txt_files) == 0:
    print("未找到任何提示词文件，请使用wd14-tagger插件（或其他类似功能）生成提示词，放入"+frame_path+"目录后重试。")
    quit()

# 输入必要的参数
denoising_strength = input("请输入重绘幅度，0 - 1之间：")
print("重绘幅度为：" + denoising_strength)
Mag = float(input("请输入图片缩放倍率，默认为1：") or 1)
print("缩放倍率为：" + str(Mag))
Set_Prompt = input("请输入正向提示词（可为空，由txt文件自动加载）：")
Neg_Prompt = input("请输入反向提示词（可为空）：")

# 输入CN的参数
print("是否使用ControlNet？\n1. 是\n2. 否")
choice = input("请做出选择：")
control_nets=[]
while True:
    if choice == "1":
        control_nets.append(get_CNmap())
        print("是否继续添加ControlNet？\n1. 是\n2. 否")
        temp=input("请做出选择：")
        if temp == "2":
            break


for frame, txt in zip(frame_files, txt_files):
    frame_file = os.path.join(frame_path,frame)
    txt_file = os.path.join(frame_path,txt)
    with open(txt_file, "r") as t:
        tag = t.read()


    # 载入单张图片基本参数
    im = Image.open(frame_file)
    encoded_image = img_str(im)
    frame_w,frame_h = im.size

    """    # 定义一个ContrlNet参数表
    control_nets = [
        ("lineart_realistic", 0.4), # 第一个CN名称和权重
        ("tile_colorfix", 0.6), # 第二个
    ]"""

    # 轮询输出ControlNet的参数
    for cn in control_nets:
        print(cn[0],cn[1],cn[2])
    cn_args = [
        {
            "input_image": encoded_image,
            "module": str(cn[0]),
            "model": str(cn[1]),
            "weight": str(cn[2]), 
            "resize_mode": 0,   # 缩放模式，0调整大小、1裁剪后缩放、2缩放后填充空白
            "processor_res": 64,
            "pixel_perfect": True,  # 完美像素模式
            "control_mode": 0,  # 控制模式，0均衡、1偏提示词、2偏CN
        } for cn in control_nets
    ]
    
    payload = {
        "init_images": [encoded_image],
        "prompt": tag + "," + Set_Prompt,  # 正向提示词，固定提示词+通过txt文件载入
        "negative_prompt": Neg_Prompt,  # 反向提示词
        "width": frame_w * Mag,   # 宽
        "height": frame_h * Mag,  # 高
        "denoising_strength": denoising_strength,   # 重绘比例
        "batch_size": 1,    # 生成张数，别改，只会留下最后一张
        "steps": 20,    # 迭代步数
        "alwayson_scripts": {
            "controlnet": {
                "args": cn_args
            }
        }
    }
    print(frame+"开始生成！生成尺寸为"+str(int(frame_w*Mag))+"x"+str(int(frame_h*Mag))+"像素")

    response = requests.post(url=f"{url}/sdapi/v1/img2img", json=payload)

    r = response.json()

    i = r["images"][0]
    image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

    png_payload = {
        "image": "data:image/png;base64," + i
    }
    response2 = requests.post(url=f"{url}/sdapi/v1/png-info", json=png_payload)
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("parameters", response2.json().get("info"))
    image.save(os.path.join(out_path,frame), pnginfo=pnginfo)
    print(frame+"生成完毕！")
print("全部图片生成完毕！共计"+str(len(frame_files))+"张！")
