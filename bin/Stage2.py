import os
import torch
import shutil
import requests
import io
import cv2
import base64
from PIL import Image, PngImagePlugin

# 检查是否有可用的CUDA设备
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("加速成功！使用的设备：CUDA")
else:
    device = torch.device("cpu")
    print("加速失败！使用的设备：CPU")

# 定义本机的SD网址
url = "http://127.0.0.1:7860"

# 定义输入文件夹
folder_path = os.path.dirname(os.getcwd())
mask_path = os.path.join(folder_path, "video_mask_w")    #定义蒙版文件夹
frame_path = os.path.join(folder_path, "video_frame_w")  #定义原始图像文件夹

# 图生图输出文件夹
out_path = os.path.join(folder_path, "video_remake")
# 蒙版文件夹存在就删除
if os.path.exists(out_path):
    shutil.rmtree(out_path)
# 不存在就创建
if not os.path.exists(out_path):
    os.makedirs(out_path)

# 轮询输入目录
frame_files = [f for f in os.listdir(frame_path) if f.endswith('.png')]
txt_files = [f for f in os.listdir(frame_path) if f.endswith('.txt')]

if len(frame_files) == 0:
    print("裁切后图片目录中没有任何图片，请检查"+frame_path+"目录后重试。")
    quit()
if len(txt_files) == 0:
    print("未找到任何提示词文件，请使用wd14-tagger插件（或其他类似功能）生成提示词，放入"+frame_path+"目录后重试。")
    quit()

# 输入重绘幅度
denoising_strength = input("请输入重绘幅度，0 - 1之间：")
print("重绘幅度为：" + denoising_strength)


for frame, txt in zip(frame_files, txt_files):
    frame_file = os.path.join(frame_path,frame)
    txt_file = os.path.join(frame_path,txt)
    with open(txt_file, 'r') as t:
        tag = t.read()

    # 载入单张图片基本参数
    im = Image.open(frame_file)
    img = cv2.imread(frame_file)
    retval, bytes = cv2.imencode('.png', img)
    encoded_image = base64.b64encode(bytes).decode('utf-8')
    frame_w,frame_h = im.size
    payload = {
        "init_images": [encoded_image], #图生图的原图
        "prompt": tag,  #提示词，来自于txt文件
        "negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",  #反向提示词，填或者不填
        "width": frame_w,   #生成的宽度，来自原图
        "height": frame_h,  #生成的高度，来自原图
        "denoising_strength": denoising_strength,   #重绘幅度
        "sampler_index": "DPM++ 2M Karras", #采样方法
        "batch_size": 1,    #生成图的数量，只能为1
        "steps": 20 #迭代步数
    }
    print(frame+"开始生成！生成尺寸为"+str(frame_w)+"x"+str(frame_h)+"像素")

    response = requests.post(url=f'{url}/sdapi/v1/img2img', json=payload)

    r = response.json()

    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))
        image.save(os.path.join(out_path,frame), pnginfo=pnginfo)
        print(frame+"生成完毕！")
print("全部图片生成完毕！共计"+str(len(frame_files))+"张！")