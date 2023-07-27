import os
import torch
import shutil
import requests
import io
import cv2
import base64
import json
from PIL import Image, PngImagePlugin

# 定义本机的SD网址
url = "http://127.0.0.1:7860"

def CNmodel_list(ex_url):
    type_url= url + ex_url
    headers = {
    "Content-Type": "application/json"
    }
    with request.urlopen(request.Request(url, json.dumps(data).encode(), headers)) as res:
        body = json.loads(res.read())
    return requests.get(url)

#r=CNmodel_list("/controlnet/control_types")

# 定义一个ContrlNet参数表
control_nets = [
    ("lineart_realistic", 0.7), # 第一个CN名称和权重
    ("tile_colorfix", 0.6), # 第二个
]

# 定义ControlNet的模型对应字典
ex_control_dict = {
    "softedge_pidinet" : "control_v11p_sd15_softedge [a8575a2a]",
    "canny" : "control_v11p_sd15_canny [d14c016b]",
    "openpose_full" : "control_v11p_sd15_openpose [cab727d4]",
    "openpose" : "control_v11p_sd15_openpose [cab727d4]",    
    "depth_midas": "control_v11f1p_sd15_depth [cfd03158]",
    "depth_zoe": "control_v11f1p_sd15_depth [cfd03158]",    
    "lineart_realistic": "control_v11p_sd15_lineart [43d4be0d]",    
    "lineart_anime": "control_v11p_sd15s2_lineart_anime [3825e83e]",        
    "normal_bae": "control_v11p_sd15_normalbae [316696f1]",
    "inpainting_global_harmonious": "controlnet_v11p_sd15_inpaint [ebff9138]",
    "tile_resample": "control_v11f1e_sd15_tile [a371b31b]",
    "tile_colorfix": "control_v11f1e_sd15_tile [a371b31b]",
    "tile_colorfix+sharp": "control_v11f1e_sd15_tile [a371b31b]",    
    "reference_only": "None",
    "reference_adain+attn": "None"
}

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

    # 轮询输出ControlNet的参数
    cn_args = [
        {
            "input_image": encoded_image,
            "module": cn[0], 
            "model": ex_control_dict[cn[0]],
            "weight": cn[1], 
        } for cn in control_nets
    ]
    
    payload = {
        "init_images": [encoded_image],
        "prompt": tag,
        "negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
        "width": frame_w,
        "height": frame_h,
        "denoising_strength": denoising_strength,
        #"sampler_index": "DPM++ 2M Karras",
        "batch_size": 1,
        "steps": 20,
        "alwayson_scripts": {
            "controlnet": {
                "args": cn_args
            }
        }
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
