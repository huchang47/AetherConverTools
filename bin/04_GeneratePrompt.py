import os
import subprocess
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
from io import BytesIO
import cv2
from PIL import Image
from pathlib import Path
from huggingface_hub import hf_hub_download


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
    # 假设图像已经经过 make_square 处理
    if img.shape[0] > size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    elif img.shape[0] < size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_CUBIC)
    return img

# 调用gpu，很难成功，环境要求太高
use_cpu = False

if use_cpu:
    tf_device_name = '/cpu:0'
else:
    tf_device_name = '/gpu:0'

class Interrogator:
    @staticmethod
    def postprocess_tags(
        tags: Dict[str, float],
        threshold=0.35, # 阈值强度，默认0.35
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

        tags = {
            t: c
            # 按标签名称或置信度排序
            for t, c in sorted(
                tags.items(),
                key=lambda i: i[0 if sort_by_alphabetical_order else 1],
                reverse=not sort_by_alphabetical_order
            )
            # 筛选大于阈值的标签
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
        Dict[str, float],
        Dict[str, float]
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
        from onnxruntime import InferenceSession
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        if not model_path.exists():
            raise FileNotFoundError(f'{model_path}不存在')
        if not tags_path.exists():
            raise FileNotFoundError(f'{tags_path}不存在')
        self.model_path = model_path
        self.tags_path = tags_path
      

        self.model = InferenceSession(str(model_path), providers=providers)

        print(f'从{model_path}下载或读取{self.name}模型')

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
        _, height, _, _ = self.model.get_inputs()[0].shape

        # 透明转换成白色
        image = image.convert('RGBA')
        new_image = Image.new('RGBA', image.size, 'WHITE')
        new_image.paste(image, mask=image)
        image = new_image.convert('RGB')
        image = np.asarray(image)

        # RGB格式转换
        image = image[:, :, ::-1]
        image = make_square(image, height)

        image = smart_resize(image, height)
        image = image.astype(np.float32)
        image = np.expand_dims(image, 0)

        # 验证一下模型
        input_name = self.model.get_inputs()[0].name
        label_name = self.model.get_outputs()[0].name
        confidents = self.model.run([label_name], {input_name: image})[0]

        tags = self.tags[:][['name']]
        tags['confidents'] = confidents[0]

        # 前4项标签用于评定模型（一般、敏感、可疑、明确）
        ratings = dict(tags[:4].values)

        # 其他的是常规标签
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

# 定义输入文件夹
folder_path = os.path.dirname(os.getcwd())
frame_path = os.path.join(folder_path, "video_frame_w")  # 定义原始图像文件夹

# 轮询开始输出
frame_files = [f for f in os.listdir(frame_path) if f.endswith(".png")]
for frame in frame_files:
    frame_file = os.path.join(frame_path, frame)
    txt= getTags(frame_file)
    tag_count= len(txt.split(","))+1
    # 创建提示词txt文件
    txt_file = os.path.join(frame_path, f'{os.path.splitext(frame_file)[0]}.txt')
    with open(txt_file, 'w', encoding='utf-8') as tags:
        tags.write(txt)
    print(f'{frame}的提示词反推完成，提取{tag_count}个tag')

# 是否进行下一步
choice = input("\n是否直接开始下一步，进行批量图生图？需要启用API后启动SD，详细配置请打开[05_BatchImg2Img]文件手动调整\n1. 是\n2. 否\n请输入你的选择：")
if choice == "1":
    subprocess.run(['python', '05_BatchImg2Img.py'])
else:
    quit()