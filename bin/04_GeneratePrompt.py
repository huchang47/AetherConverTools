import base64
import os
<<<<<<< HEAD
import subprocess
=======
import torch
import subprocess
import pandas as pd
import numpy as np

from typing import Tuple, List, Dict
>>>>>>> ad2e6919ba879390be4202a1dd08bf84bef69f5d
from io import BytesIO
import requests
from PIL import Image
<<<<<<< HEAD
=======

from pathlib import Path
from huggingface_hub import hf_hub_download
>>>>>>> ad2e6919ba879390be4202a1dd08bf84bef69f5d

# 定义本机的SD网址
url = 'http://127.0.0.1:7860'   #本机SD的地址，如果修改了或者使用网络地址，请修改此处
ex_url = url + "/tagger/v1/interrogate"
headers = {
    'accept': 'application'
}
requests.post(f"{url}/tagger/v1/unload-interrogators", headers=headers)

<<<<<<< HEAD
# 定义WD模型接口
def listwd():
    wd_list = requests.get(f"{url}/tagger/v1/interrogators").json()
    return wd_list
=======
def make_square(img, target_size):
    old_size = img.shape[:2]
    desired_size = max(old_size)
    desired_size = max(desired_size, target_size)

    delta_w = desired_size - old_size[1]
    delta_h = desired_size - old_size[0]
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    color = [255, 255, 255]
    new_im = cv2.copyMakeBorder(
        img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
    )
    return new_im


def smart_resize(img, size):
    # Assumes the image has already gone through make_square
    if img.shape[0] > size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    elif img.shape[0] < size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_CUBIC)
    return img

# select a device to process
use_cpu = False

if use_cpu:
    tf_device_name = '/cpu:0'
else:
    tf_device_name = '/gpu:0'

class Interrogator:
    @staticmethod
    def postprocess_tags(
        tags: Dict[str, float],

        threshold=0.25,
        additional_tags: List[str] = [],
        exclude_tags: List[str] = [],
        sort_by_alphabetical_order=False,
        add_confident_as_weight=False,
        replace_underscore=False,
        replace_underscore_excludes: List[str] = [],
        escape_tag=False
    ) -> Dict[str, float]:
        for t in additional_tags:
            tags[t] = 1.0

        # those lines are totally not "pythonic" but looks better to me
        tags = {
            t: c

            # sort by tag name or confident
            for t, c in sorted(
                tags.items(),
                key=lambda i: i[0 if sort_by_alphabetical_order else 1],
                reverse=not sort_by_alphabetical_order
            )

            # filter tags
            if (
                c >= threshold
                and t not in exclude_tags
            )
        }

        new_tags = []
        for tag in list(tags):
            new_tag = tag

            if replace_underscore and tag not in replace_underscore_excludes:
                new_tag = new_tag.replace('_', ' ')

            """
            if escape_tag:
                new_tag = tag_escape_pattern.sub(r'\\\1', new_tag)
            """
            if add_confident_as_weight:
                new_tag = f'({new_tag}:{tags[tag]})'

            new_tags.append((new_tag, tags[tag]))
        tags = dict(new_tags)

        return tags

    def __init__(self, name: str) -> None:
        self.name = name

    def load(self):
        raise NotImplementedError()

    def unload(self) -> bool:
        unloaded = False

        if hasattr(self, 'model') and self.model is not None:
            del self.model
            unloaded = True
            print(f'Unloaded {self.name}')

        if hasattr(self, 'tags'):
            del self.tags

        return unloaded

    def interrogate(
        self,
        image: Image
    ) -> Tuple[
        Dict[str, float],  # rating confidents
        Dict[str, float]  # tag confidents
    ]:
        raise NotImplementedError()


class WaifuDiffusionInterrogator(Interrogator):
    def __init__(
        self,
        name: str,
        model_path='model.onnx',
        tags_path='selected_tags.csv',
        **kwargs
    ) -> None:
        super().__init__(name)
        self.model_path = model_path
        self.tags_path = tags_path
        self.kwargs = kwargs

    def download(self) -> Tuple[os.PathLike, os.PathLike]:
        print(f"Loading {self.name} model file from {self.kwargs['repo_id']}")

        model_path = Path(hf_hub_download(
            **self.kwargs, filename=self.model_path))
        tags_path = Path(hf_hub_download(
            **self.kwargs, filename=self.tags_path))
        return model_path, tags_path

    def load(self) -> None:
        model_path, tags_path = self.download()

        # only one of these packages should be installed at a time in any one environment
        # https://onnxruntime.ai/docs/get-started/with-python.html#install-onnx-runtime
        # TODO: remove old package when the environment changes?

        from onnxruntime import InferenceSession

        # https://onnxruntime.ai/docs/execution-providers/
        # https://github.com/toriato/stable-diffusion-webui-wd14-tagger/commit/e4ec460122cf674bbf984df30cdb10b4370c1224#r92654958
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        if tf_device_name == '/cpu:0':
            providers.pop(0)

        self.model = InferenceSession(str(model_path), providers=providers.pop(1))

        print(f'Loaded {self.name} model from {model_path}')

        self.tags = pd.read_csv(tags_path)

    def interrogate(
        self,
        image: Image
    ) -> Tuple[
        Dict[str, float],  # rating confidents
        Dict[str, float]  # tag confidents
    ]:
        # init model
        if not hasattr(self, 'model') or self.model is None:
            self.load()

        # code for converting the image and running the model is taken from the link below
        # thanks, SmilingWolf!
        # https://huggingface.co/spaces/SmilingWolf/wd-v1-4-tags/blob/main/app.py

        # convert an image to fit the model
        _, height, _, _ = self.model.get_inputs()[0].shape

        # alpha to white
        image = image.convert('RGBA')
        new_image = Image.new('RGBA', image.size, 'WHITE')
        new_image.paste(image, mask=image)
        image = new_image.convert('RGB')
        image = np.asarray(image)

        # PIL RGB to OpenCV BGR
        image = image[:, :, ::-1]
        image = make_square(image, height)

        image = smart_resize(image, height)
        image = image.astype(np.float32)
        image = np.expand_dims(image, 0)

        # evaluate model
        input_name = self.model.get_inputs()[0].name
        label_name = self.model.get_outputs()[0].name
        confidents = self.model.run([label_name], {input_name: image})[0]

        tags = self.tags[:][['name']]
        tags['confidents'] = confidents[0]

        # first 4 items are for rating (general, sensitive, questionable, explicit)
        ratings = dict(tags[:4].values)

        # rest are regular tags
        tags = dict(tags[4:].values)

        return ratings, tags


my_wf =  WaifuDiffusionInterrogator(
            'wd14-convnextv2-v2',
            repo_id='SmilingWolf/wd-v1-4-convnextv2-tagger-v2',
            revision='v2.0'
        )

def getTags(img_path):
    global my_wf
    img = Image.open(img_path)
    ratings, tags = my_wf.interrogate(img)
    tags = my_wf.postprocess_tags(tags)
    
    return ",".join(tags.keys())
>>>>>>> ad2e6919ba879390be4202a1dd08bf84bef69f5d

# 定义输入文件夹
folder_path = os.path.dirname(os.getcwd())
frame_path = os.path.join(folder_path, "video_frame_w")  # 定义原始图像文件夹

# 定义获取WdTagger模型函数
def get_WDmap():
    WD_model = {}
    num = 0
    data = listwd()['models']
    for i in data:
        WD_model[num] = i
        print(str(num) + ". ", i)
        num += 1
    Choice = int(input("请选择WD模型编号："))
    print("选择的是", WD_model[Choice], "缺少的模型会自动下载")
    return WD_model[Choice]

# 定义wd14的参数
model = get_WDmap()
threshold = 0.5  # 识别强度阈值，可自行调整

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
    response = ''
    caption_dict = {}
    sorted_items = []
    frame_file = os.path.join(frame_path, frame)
<<<<<<< HEAD
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
        # 处理返回的JSON数据

        caption_dict = response.json()['caption']
        sorted_items = sorted([(k, v) for k, v in caption_dict.items() if float(v) > threshold], key=lambda x: x[1],
                              reverse=True)
        txt = ','.join([f'{k}' for k, v in sorted_items])

        # 创建提示词txt文件
        txt_file = os.path.join(frame_path, f'{os.path.splitext(frame_file)[0]}.txt')
        with open(txt_file, 'w', encoding='utf-8') as tags:
            tags.write(txt)
        print(f'{frame}的提示词反推完成，提取{len(sorted_items)}个tag')
    else:
        print('错误:', response.status_code)
        print('返回内容:', response.text)

=======
    txt= getTags(frame_file)
    tag_count= len(txt.split(","))+1
    # 创建提示词txt文件
    txt_file = os.path.join(frame_path, f'{os.path.splitext(frame_file)[0]}.txt')
    with open(txt_file, 'w', encoding='utf-8') as tags:
        tags.write(txt)
    print(f'{frame}的提示词反推完成，提取{tag_count}个tag')
    
>>>>>>> ad2e6919ba879390be4202a1dd08bf84bef69f5d
# 是否进行下一步
choice = input("\n是否直接开始下一步，进行批量图生图？需要启用API后启动SD，详细配置请打开[05_BatchImg2Img]文件手动调整\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '05_BatchImg2Img.py'])
else:
    quit()