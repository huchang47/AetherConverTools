import os
import re
import subprocess
import sys

import pandas as pd
import numpy as np
from typing import Tuple, List, Dict
from io import BytesIO
import cv2
from PIL import Image
from pathlib import Path
from huggingface_hub import hf_hub_download

from common_utils import prefer_device
from common_config import *


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
            threshold=0.35,  # 阈值强度，默认0.35
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


def getTags(model, img_path):
    img = Image.open(img_path)
    ratings, tags = model.interrogate(img)
    img.close()
    tags = model.postprocess_tags(tags)
    return ",".join(tags.keys())


pattern_word_split = re.compile(r"\W+")


def is_tag_in_list(tag, rule_list):
    words = pattern_word_split.split(tag)
    for word in words:
        if word in rule_list:
            return True
    return False


def filter_action(tag_actions:[], tags: []):
    action_tags = []
    other_tags = []
    for tag in tags:
        if is_empty(tag):
            continue
        if is_tag_in_list(tag, tag_actions):
            action_tags.append(tag)
        else:
            other_tags.append(tag)
    return action_tags, other_tags


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Params: <runtime-config.json>")
        exit(ERROR_PARAM_COUNT)

    it_mode = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        setting_json = read_config(sys.argv[1], webui=False)
    except Exception as e:
        print("Error: read config", e)
        exit(ERROR_READ_CONFIG)

    device = prefer_device()

    setting_config = SettingConfig(setting_json)

    # workspace path config
    workspace = setting_config.get_workspace_config()

    if not os.path.exists(workspace.input_tag):
        os.makedirs(workspace.input_tag)

    # 可选功能
    if setting_config.enable_tag():

        # load model
        model = WaifuDiffusionInterrogator(
            'wd14-convnextv2-v2',
            repo_id='SmilingWolf/wd-v1-4-convnextv2-tagger-v2',
            revision='v2.0'
        )

        tag_mode = setting_config.get_tag_mode()
        tag_actions = setting_config.get_tag_actions()

        # 轮询开始输出
        frame_files = [f for f in os.listdir(workspace.input_crop) if f.endswith(".png")]
        frame_files.sort()

        common_tags = dict()
        for frame in frame_files:
            frame_file = os.path.join(workspace.input_crop, frame)
            txt = getTags(model, frame_file)
            tags = txt.split(",")

            if tag_mode == TAG_MODE_ACTION:
                actions, others = filter_action(tag_actions, tags)
                # 替换 txt 为 action txt
                txt = ",".join(actions) if len(actions) > 0 else ""
            elif tag_mode == TAG_MODE_ACTION_COMMON:
                actions, others = filter_action(tag_actions, tags)
                txt = ",".join(actions) if len(actions) > 0 else ""
                # tag 计数
                for tag in others:
                    if tag in common_tags:
                        common_tags[tag] = common_tags[tag] + 1
                    else:
                        common_tags[tag] = 1

            # save tag
            txt_file = os.path.join(workspace.input_tag, f'{Path(frame_file).stem}.txt')
            with open(txt_file, 'w', encoding='utf-8') as tags:
                tags.write(txt)
            # tag_count = len(txt.split(","))+1
            print(f'{frame} 提示词反推完成')

        # 过滤出现次数 > 30% 的 tags 作为 common tags
        threshold_count = max(int(len(frame_files) * 0.3), 1)
        common_tag_list = []
        for tag in common_tags:
            if common_tags[tag] > threshold_count:
                common_tag_list.append(tag)
        # save common tag
        txt_file = os.path.join(workspace.input_tag, f'common.txt')
        with open(txt_file, 'w', encoding='utf-8') as tags:
            txt = ",".join(common_tag_list) if len(common_tag_list) > 0 else ""
            tags.write(txt)

    if it_mode is None:
        it_mode = setting_config.get_interactive_mode()
    if it_mode == INTERACTIVE_MODE_INPUT:
        # 是否进行下一步
        choice = input("\n是否直接开始下一步，进行批量图生图？需要启用API后启动SD，详细配置请打开[05_BatchImg2Img]文件手动调整\n1. 是\n2. 否\n请输入你的选择：")
        if choice != "1":
            exit(0)
    subprocess.run(['python', '05_BatchImg2Img.py', sys.argv[1]])
