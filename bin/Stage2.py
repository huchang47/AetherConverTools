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

def CNmodel_list(ex_url):
    type_url= url + ex_url
    headers = {
    "Content-Type": "application/json"
    }
    with request.urlopen(request.Request(url, json.dumps(data).encode(), headers)) as res:
        body = json.loads(res.read())
    return requests.get(url)

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
frame_files = [f for f in os.listdir(frame_path) if f.endswith('.png')]
txt_files = [f for f in os.listdir(frame_path) if f.endswith('.txt')]

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
print("是否启用ADetailer进行脸部修复（请确保你正确安装了该插件，否则可能出错）？\n1. 是\n2. 否")
ADe_type = input("请输入选择编号：")
if ADe_type == '1':
    Ade_Mod= 'mediapipe_face_full'  # 写死Ade调用的模型，别去选择了，差异不大。有特殊需求自己改这里。
    print(f"使用ADetailer的{Ade_Mod}模型进行脸部修复")
else:
    Ade_Mod='None'

for frame, txt in zip(frame_files, txt_files):
    frame_file = os.path.join(frame_path,frame)
    txt_file = os.path.join(frame_path,txt)
    with open(txt_file, 'r') as t:
        tag = t.read()


    # 载入单张图片基本参数
    im = Image.open(frame_file)
    encoded_image = img_str(im)
    frame_w,frame_h = im.size

    # 定义一个ContrlNet参数表
    control_nets = [
        ("None", 0.4), # 默认为不调用任何CN，避免没有模型报错。有能力的自己改：第一个CN名称和权重，多个CN就同样加一行。
]
    # 定义ADetailer的参数
    Ade_args = [
        {
            "ad_model": Ade_Mod,
            "ad_confidence": 0.5,
        }
    ]

    # 轮询输出ControlNet的参数
    if control_nets[0][0]== 'None':
        cn_args=[]
    else:
        cn_args = [
            {
                "input_image": encoded_image,
                "module": cn[0], 
                "model": ex_control_dict[cn[0]],
                "weight": cn[1], 
                "resize_mode": 0,   # 缩放模式，0调整大小、1裁剪后缩放、2缩放后填充空白
                "processor_res": 64,
                "pixel_perfect": True,  # 完美像素模式
                "control_mode": 0,  # 控制模式，0均衡、1偏提示词、2偏CN
                "guidance_start": 0.0,  # 引导介入时机
                "guidance_end": 1.0,    # 引导终止时机
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
            },
            "ADetailer": {
                "args": Ade_args
            }
        }
    }
    print(frame+"开始生成！生成尺寸为"+str(int(frame_w*Mag))+"x"+str(int(frame_h*Mag))+"像素")

    response = requests.post(url=f'{url}/sdapi/v1/img2img', json=payload)

    r = response.json()

    i = r['images'][0]
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
