import os
import io
import requests
import base64
from io import BytesIO
from collections import OrderedDict
from PIL import Image, PngImagePlugin

# 定义本机的SD网址
url = 'http://127.0.0.1:7860'
ex_url = url + "/tagger/v1/interrogate"

# 定义WD模型接口
def ListWD():
    wd_list = requests.get(f"{url}/tagger/v1/interrogators").json()
    return wd_list

# 定义输入文件夹
folder_path = os.path.dirname(os.getcwd())
frame_path = os.path.join(folder_path, "video_frame_w")  #定义原始图像文件夹

# 定义获取WdTagger模型函数
def get_WDmap():
    WD_model={}
    num=0
    data=ListWD()['models']
    for i in data:
        WD_model[num]=i
        print(str(num)+". ",i)
        num+=1
    Choice= int(input("请选择WD模型编号："))
    print("选择的是",WD_model[Choice])
    return WD_model[Choice]
    
# 定义wd14的参数
model = get_WDmap()
threshold = 0.35    # 识别强度

# 定义图片转base64函数
def img_str(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# 轮询目录开始输出
frame_files = [f for f in os.listdir(frame_path) if f.endswith(".png")]

if len(frame_files) == 0:
    print(f"裁切后图片目录中没有任何图片，请检查{frame_path}目录后重试。")
    quit()

for frame in frame_files:
    frame_file = os.path.join(frame_path,frame)
    img = img_str(Image.open(frame_file))

    with open(frame_file, 'rb') as file:
        image_data = file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
# 构建请求体的JSON数据
    data = {
        "image": base64_image,
        "model": model,
        "threshold": threshold,
    }

    # 请求接口返回内容
    response = requests.post(ex_url, json=data)

    # 检查响应状态码
    if response.status_code == 200:
        json_data = response.json()
        # 处理返回的JSON数据
        caption_dict = json_data['caption']
        sorted_items = sorted([(k, v) for k, v in caption_dict.items() if float(v/100) > threshold], key=lambda x: x[1], reverse=True)
        txt = ','.join([f'{k}' for k, v in sorted_items])

        # 创建提示词txt文件
        txt_file=os.path.join(frame_path,f'{frame_file.split(".")[0]}.txt')
        with open(txt_file, 'w', encoding='utf-8') as tags:
            tags.write(txt)
        print(f'{frame}的提示词反推完成，提取{len(sorted_items)}个tag')


    else:
        print('错误:', response.status_code)
        print('返回内容:', response.text)