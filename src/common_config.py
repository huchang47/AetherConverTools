import json
import os
import copy
from math import lcm

import requests

from image_utils import round_up

ERROR_PARAM_COUNT = 1
ERROR_READ_CONFIG = 2
ERROR_WEBUI_API = 3
ERROR_INPUT_EMPTY = 4
ERROR_WEBUI_CALL = 5
ERROR_NO_VIDEO = 6
ERROR_UNKNOWN_MASK_MODE = 7

def is_empty(obj):
    if obj is None:
        return True
    elif isinstance(obj, str):
        return len(obj) == 0
    elif isinstance(obj, list):
        return len(obj) == 0
    elif isinstance(obj, dict):
        return len(obj) == 0
    return False

def opt_dict(obj, key, default=None):
    if obj is None:
        return default
    if key in obj:
        v = obj[key]
        if not is_empty(v):
            return v
    return default


def read_config(path, webui=True):
    with open(path, 'r', encoding='utf-8') as f:
        runtime_config = json.load(f)

    if "config" not in runtime_config:
        print("no filed 'config' in json")
        return None

    config = runtime_config["config"]
    if "webui" not in config:
        print("no filed 'webui' in 'config'")
        return None

    if "setting" not in config:
        print("no filed 'setting' in 'config'")
        return None

    setting_config_path = config["setting"]
    if not os.path.exists(setting_config_path):
        setting_config_path = "config/setting/" + setting_config_path
        if not os.path.exists(setting_config_path):
            setting_config_path = "../" + setting_config_path

    # read config
    with open(setting_config_path, 'r', encoding='utf-8') as f:
        setting_config = json.load(f)

    # set workspace parent:根目录
    if "workspace" in setting_config:
        setting_config["workspace"]["parent"] = runtime_config["workspace"]
    else:
        setting_config["workspace"] = {
            "parent": runtime_config["workspace"]
        }
    setting_config["video"] = opt_dict(runtime_config, "video")

    # merge setting config
    if "setting" in config:
        setting_config.update(runtime_config["setting"])

    # webui config
    if webui:
        webui_config_path = config["webui"]
        if not os.path.exists(webui_config_path):
            webui_config_path = "config/webui/" + webui_config_path
            if not os.path.exists(webui_config_path):
                webui_config_path = "../" + webui_config_path

        with open(webui_config_path, 'r', encoding='utf-8') as f:
            webui_config = json.load(f)

        # merge webui config
        if "webui" in runtime_config:
            webui_config.update(runtime_config["webui"])

        return webui_config, setting_config

    return setting_config


class VideoConfig:

    def __init__(self, config: dict):
        self.config = config

    def get_input(self):
        return opt_dict(self.config, "input")

    def get_fps(self):
        return opt_dict(self.config, "fps", 15)

    def get_output(self):
        return opt_dict(self.config, "output", "output.mp4")

    def enable_audio(self):
        return opt_dict(self.config, "audio", True)

# 工作路径
class Workspace:

    def __init__(self, root: str, input: str, output: str, input_crop: str, output_crop: str,
                 input_tag: str, input_mask: str, input_crop_mask: str, crop_info: str):
        self.root = root
        self.input = input
        self.output = output
        self.input_crop = input_crop
        self.output_crop = output_crop
        self.input_tag = input_tag
        self.input_mask = input_mask
        self.input_crop_mask = input_crop_mask
        self.crop_info = crop_info


MASK_MODE_TRANSPARENT_BACKGROUND = "transparent-background"
MASK_MODE_TRANSPARENT_BACKGROUND_FAST = "transparent-background-fast"
MASK_MODE_SAM = "sam"
MASK_MODE_PURE = "pure"

MASK_BG_MODE_NONE = ""
MASK_BG_MODE_TRANSPARENT = "transparent"

TAG_MODE_NONE = ""
TAG_MODE_ACTION = "action"
TAG_MODE_ACTION_COMMON = "action_common"

INTERACTIVE_MODE_AUTO = "auto"
INTERACTIVE_MODE_INPUT = "input"

CROP_MODE_NONE = 0
CROP_MODE_MIN = 1
CROP_MODE_ACCORDANT = 2

DRAW_TYPE_IMG2IMG = "img2img"
DRAW_TYPE_TXT2IMG = "txt2img"

# 策略参数设置配置
class SettingConfig:

    def __init__(self, config: dict):
        self.config = config
        self.webui_work_api = None

    def get_interactive_mode(self):
        return opt_dict(self.config, "interactive_mode", INTERACTIVE_MODE_AUTO)

    def get_draw_type(self):
        return opt_dict(self.config, "type", DRAW_TYPE_IMG2IMG)

    def is_img2img(self):
        return self.get_draw_type() == DRAW_TYPE_IMG2IMG

    def get_webui_api(self):
        if self.webui_work_api is None:
            webui_api = opt_dict(self.config, "webui_api_url", "http://127.0.0.1:7860/")
            draw_type = self.get_draw_type()
            if draw_type == DRAW_TYPE_IMG2IMG:
                path = "sdapi/v1/img2img"
            elif draw_type == DRAW_TYPE_TXT2IMG:
                path = "sdapi/v1/txt2img"
            else:
                print("Error: webui api type error")
                return None
            self.webui_work_api = webui_api + path
        return self.webui_work_api

    def get_current_seed(self):
        seed = opt_dict(self.config, "seed", -1)
        if seed == 1:
            seed = -1
        return seed

    def fix_first_seed(self):
        return 1 == opt_dict(self.config, "seed", -1)

    def set_seed(self, seed):
        self.config["seed"] = seed

    def get_mask_mode(self):
        return opt_dict(self.config, "mask_mode", MASK_MODE_TRANSPARENT_BACKGROUND)

    def get_mask_bg_mode(self):
        return opt_dict(self.config, "mask_bg_mode", MASK_BG_MODE_NONE)

    def get_tag_mode(self):
        tag_cfg = opt_dict(self.config, "tag")
        return opt_dict(tag_cfg, "mode", TAG_MODE_NONE)

    def get_tag_actions(self):
        tag_cfg = opt_dict(self.config, "tag")
        return opt_dict(tag_cfg, "actions", [])

    def get_workspace_config(self) -> Workspace:
        workspace_config = opt_dict(self.config, "workspace")
        tmp_config = opt_dict(workspace_config, "tmp")

        input = opt_dict(workspace_config, "input", "input")
        output = opt_dict(workspace_config, "output", "output")
        workspace_parent = opt_dict(workspace_config, "parent", "")

        tmp_parent = opt_dict(tmp_config, "parent", "tmp")
        input_crop = opt_dict(tmp_config, "input_crop", "input_crop")
        output_crop = opt_dict(tmp_config, "output_crop", "output_crop")
        input_tag = opt_dict(tmp_config, "input_tag", "input_crop")
        input_mask = opt_dict(tmp_config, "input_mask", "input_mask")
        input_crop_mask = opt_dict(tmp_config, "input_crop_mask", "input_crop_mask")
        crop_info = opt_dict(tmp_config, "crop_info", "crop_info.txt")

        tmp_path = os.path.join(workspace_parent, tmp_parent)

        return Workspace(workspace_parent, os.path.join(workspace_parent, input), os.path.join(workspace_parent, output),
                         os.path.join(tmp_path, input_crop), os.path.join(tmp_path, output_crop),
                         os.path.join(tmp_path, input_tag), os.path.join(tmp_path, input_mask),
                         os.path.join(tmp_path, input_crop_mask), os.path.join(tmp_path, crop_info))

    def get_size_scale(self, w, h):
        resize_config = opt_dict(self.config, "resize")
        if resize_config is None:
            return w, h, 1, 1

        scale_w = opt_dict(resize_config, "width", 0)
        scale_h = opt_dict(resize_config, "height", 0)
        if scale_w == 0 and scale_h == 0:
            scale_fw = scale_fh = opt_dict(resize_config, "scale", 1)
            scale_w = int(w * scale_fw)
            scale_h = int(h * scale_fh)
        elif scale_w == 0:
            scale_fw = scale_fh = scale_h / h
            scale_w = int(w * scale_fw)
        elif scale_h == 0:
            scale_fw = scale_fh = scale_w / w
            scale_h = int(h * scale_fh)

        scale_w = round_up(scale_w, 8)
        scale_h = round_up(scale_h, 8)
        scale_fw = scale_w / w
        scale_fh = scale_h / h
        return scale_w, scale_h, scale_fw, scale_fh

    def get_video(self):
        return VideoConfig(opt_dict(self.config, "video"))

    def enable_crop(self):
        return opt_dict(self.config, "crop", CROP_MODE_NONE) > CROP_MODE_NONE

    def get_crop_mode(self):
        return opt_dict(self.config, "crop", CROP_MODE_NONE)

    def enable_inpaint(self):
        return opt_dict(self.config, "inpaint", False)

    def enable_tag(self):
        tag_cfg = opt_dict(self.config, "tag")
        return opt_dict(tag_cfg, "enable", False)

    def enable_multi_frame(self):
        return opt_dict(self.config, "multi_frame", False)

    def enable_overlay(self):
        return opt_dict(self.config, "overlay", False)


class WebuiConfig:

    def __init__(self, config: dict):
        self.config = config

    def get_config(self):
        return self.config

    def inflate_control_nets(self, cur_img_ori, last_img_tra=None, cur_mask_ori=None, last_mask_tra=None):
        alwayson_scripts = opt_dict(self.config, "alwayson_scripts")
        controlnet = opt_dict(alwayson_scripts, "controlnet")
        controlnet_args = opt_dict(controlnet, "args")
        if not is_empty(controlnet_args):
            control_nets = []
            for arg in controlnet_args:
                item = copy.deepcopy(arg)
                if item['input_image'] == '{current_image_origin}':
                    if cur_img_ori is None:
                        del item['input_image']
                    else:
                        item['input_image'] = cur_img_ori
                    if cur_mask_ori is not None:
                        item['mask'] = cur_mask_ori
                elif item['input_image'] == '{previous_image_transformed}':
                    if last_img_tra is None:
                        continue
                    item['input_image'] = last_img_tra
                    if last_mask_tra is not None:
                        item['mask'] = last_mask_tra
                control_nets.append(item)
            # write back
            controlnet["args"] = control_nets

    def inflate_base(self, img, w, h, seed):
        self.config.update({
            "width": w,
            "height": h,
            "seed": seed,
        })
        if img is not None:
            self.config["init_images"] = [img]


    def inflate_mask(self, mask):
        self.config.update({
            "mask": mask,
            "inpainting_mask_invert": 0,  # 蒙版模式 0重绘蒙版内容 1 重绘非蒙版内容
            "inpainting_fill": 1,  # 蒙版遮住的内容， 0填充， 1原图 2潜空间噪声 3潜空间数值零
            "inpaint_full_res": True,  # inpaint area, False: whole picture True：only masked
            "inpaint_full_res_padding": 32,  # Only masked padding, pixels 32
        })

    def get_prompt(self):
        return opt_dict(self.config, "prompt")

    def set_prompt(self, prompt):
        self.config["prompt"] = prompt

    def call(self, url: str):
        response = requests.post(url=url, json=self.get_config())
        return response
