import os
import requests
import io
import glob
import base64
import subprocess
from io import BytesIO
from PIL import Image, PngImagePlugin

# 定义本机的SD网址
url = input("请填入你的SD地址（默认http://127.0.0.1:7860）：") or 'http://127.0.0.1:7860'
txt2img_url = f"{url}/sdapi/v1/txt2img"
img2img_url = f"{url}/sdapi/v1/img2img"

# 定义CN模型数据接口
def ListCN():
    cn_url = url + "/controlnet/control_types"
    CN_list = requests.get(url=cn_url).json()
    return CN_list

# 定义获取本地CN数据函数
def get_CNmap():
    control_dict={}
    data=ListCN()["control_types"]
    for k in data:
        if k!="All":
            for p in data[k]["module_list"]:
                if p!= "none":
                    control_dict[p] = data[k]["default_model"]
    return control_dict
    

# 定义输入文件夹
folder_path = os.path.dirname(os.getcwd())
mask_path = os.path.join(folder_path, "video_mask_w")    #定义蒙版文件夹
frame_path = os.path.join(folder_path, "video_frame_w")  #定义原始图像文件夹
image_template = os.path.join(folder_path, "00001.png")     # 定义第一个用于模版的图

# 定义图片转base64函数
def img_str(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# 定义智能倍率函数
def Get_Vam(image,tar_size,types):
    img=Image.open(image)
    w,h=img.size
    ratio_o=w/h
    if types == 1:
        # 长边方案：将长边缩放到该尺寸
        if ratio_o>=1: # 横屏
            Get_Vam=tar_size/w
        else:   #竖屏
            Get_Vam=tar_size/h
    else:
        # 短边方案：将短边缩小到该尺寸，原本就小的不调整
        min_size = min(w,h,tar_size)
        if min_size == tar_size:
            Get_Vam = tar_size/min(w,h)
        else:
            Get_Vam = 1
    return Get_Vam

# 图生图输出文件夹
out_path = os.path.join(folder_path, "video_remake")
# 不存在就创建
if not os.path.exists(out_path):
    os.makedirs(out_path)

# 判断是否已经有文件了
png_files = glob.glob(os.path.join(out_path, '*.png'))
if len(png_files)>0:
    choice = input(f"{out_path}文件夹内已有文件，再次生成会覆盖此前的图像，你确定这样做吗？\n1. 是的，我明白\n2. 别，我的图还要\n请谨慎输入你的选择：")
    if choice != '1':
        quit()


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
Choice=input("\n请选择进行文生图还是图生图？\n1. 文生图\n2. 图生图\n请输入你的选择：")
if Choice == '1':
    work_type='txt'
    work_url=txt2img_url
    denoising_strength = 0
elif Choice == '2':
    work_type='img'
    work_url=img2img_url
    denoising_strength = input("请输入重绘幅度，0 - 1之间：") or 1
    print("重绘幅度为：" + denoising_strength)
else:
    print("明智的选择，养护显卡很重要")
    quit()

# 智能倍率
Choice=input("\n是否使用智能动态倍率（指定一个尺寸，智能调整每张图输出时向该尺寸趋近）？\n1. 是\n2. 否\n请输入你的选择：")
if Choice == '1':
    vam_status = True
    try:
        types = int(input("\n请选择智能动态倍率的方案：\n1. 长边缩放方案（大图小图的长边都缩放到该尺寸）\n2. 短边缩小方案（大图的短边缩小，小图不调整）\n请输入你的选择："))
    except ValueError:
        types = 1  # 默认值
    try:
        target = int(input("\n请根据自身需求和显卡实力输入目标分辨率（720或1080或更高，默认720）："))
    except ValueError:
        target = 720  # 默认值

else:
    vam_status = False
if vam_status == False:
    Mag = float(input("请输入图片固定缩放倍率，默认为1：") or 1)
    print("固定缩放倍率为：" + str(Mag))

Set_Prompt = input("\n请输入正向提示词（可为空，由txt文件自动加载）：")
Neg_Prompt = input("请输入反向提示词（可为空）：")
print("\n是否启用ADetailer进行脸部修复（请确保你正确安装了该插件，否则可能出错）？\n1. 是\n2. 否")
ADe_type = input("请输入选择编号：") 
if ADe_type == '1':
    Ade_Mod= 'mediapipe_face_full'  # 写死Ade调用的模型，别去选择了，差异不大。有特殊需求自己改这里。
    print(f"使用ADetailer的{Ade_Mod}模型进行脸部修复")
else:
    Ade_Mod='None'

# 定义ControlNet的模型对应字典
control_dict= get_CNmap()
# print(control_dict)

# 内门心法
Choice=input("\n是否使用以太内门心法？(测试中功能)\n1. 是\n2. 否\n请输入你的选择：")
if Choice == '1':
    tmp_type = True
else:
    tmp_type = False

# 载入样板图像
if tmp_type == True:
    encoded_image_template = img_str(Image.open(image_template))

# 轮询开始出图
for frame, txt in zip(frame_files, txt_files):
    frame_file = os.path.join(frame_path,frame)
    txt_file = os.path.join(frame_path,txt)
    im = Image.open(frame_file)
    encoded_image = img_str(im)
    with open(txt_file, 'r') as t:
        tag = t.read()
    
    if vam_status == True:
        Mag=Get_Vam(frame_file,target,types)

    # 载入单张图片基本参数
    frame_w,frame_h = im.size

    # 定义一个ContrlNet参数表
    control_nets = [
        ("lineart_realistic", 0.6,0,encoded_image), # 默认为不调用任何CN，避免没有模型报错。有能力的自己改：CN名称和权重，多个CN就同样加一行。
        ("tile_colorfix", 0.6,8,encoded_image),
    ]
    # 定义ADetailer的参数
    Ade_args = [
        {
            "ad_model": Ade_Mod,    # Ade模型
            "ad_confidence": 0.5,   # 检测幅度
            "ad_prompt": "",    # Ade提示词
        }
    ]

    # 轮询输出ControlNet的参数
    if control_nets[0][0]== 'None':
        cn_args=[]
    else:
        cn_args = [
            {
                "input_image": cn[3],
                "module": cn[0], 
                "model": control_dict[cn[0]],
                "weight": cn[1], 
                "threshold_a": cn[2],
                "resize_mode": 0,   # 缩放模式，0调整大小、1裁剪后缩放、2缩放后填充空白
                "processor_res": 64,
                "pixel_perfect": True,  # 完美像素模式
                "control_mode": 0,  # 控制模式，0均衡、1偏提示词、2偏CN
                "guidance_start": 0.0,  # 引导介入时机
                "guidance_end": 1.0,    # 引导终止时机
            } for cn in control_nets
        ]
        if tmp_type == True:
            tmp_args = [    # 内门心法参数
                {
                "input_image": encoded_image_template,
                "module": "none",   # 别动
                "model": "temporalnet", # 别动
                "weight": 0.6,  # 权重
                "pixel_perfect": True,  # 完美像素模式
                }
            ]
            cn_args.extend(tmp_args)
    
    # 提取脚本的定义项目
    alwayson_scripts_args = {
        "controlnet":{
            "args": cn_args,
        },
    }
    if ADe_type == '1':
        alwayson_scripts_args.update({
            "Adetailer":{
                "args":Ade_args
            },
        })
    
    payload = {
        "init_images": [encoded_image],
        "prompt": tag + "," + Set_Prompt,  # 正向提示词，固定提示词+通过txt文件载入
        "negative_prompt": Neg_Prompt,  # 反向提示词
        "width": frame_w * Mag,   # 宽
        "height": frame_h * Mag,  # 高
        "denoising_strength": denoising_strength,   # 重绘比例
        "sampler_name": "Euler a",  # 采样方法
        "batch_size": 1,    # 生成张数，别改，只会留下最后一张
        "steps": 30,    # 迭代步数
        "cfg_scale": 7, # 提示词引导系数（CFG）
        "seed": -1, # 种子，默认随机
        "alwayson_scripts": alwayson_scripts_args
    }
    print(frame+"开始生成！生成尺寸为"+str(int(frame_w*Mag))+"x"+str(int(frame_h*Mag))+"像素")

    response = requests.post(url=work_url, json=payload)

    r = response.json()


    try:
        i = r['images'][0]
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("Parameters: ", response2.json().get("info"))
        image.save(os.path.join(out_path,frame), pnginfo=pnginfo)
        encoded_image_template = img_str(image)
        print(frame+"生成完毕！")
    except Exception as e:
        print(f"错误：处理图生图时出现异常，请查看SD控制台报错信息。")
        print(str(e))
        quit()     
print("全部图片生成完毕！共计"+str(len(frame_files))+"张！")

# 是否进行下一步
choice = input("\n是否直接开始下一步，将图生图后的图像与裁切图片进行尺寸对齐？\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '06_ResizeImage.py'])
else:
    quit()
