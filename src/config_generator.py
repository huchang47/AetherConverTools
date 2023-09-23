from common_config import *
import sys

if __name__ == '__main__':
    new_cfg = True
    if len(sys.argv) > 1:
        if int(sys.argv[1]) == 1:
            new_cfg = False

    runtime_json = dict()

    # config name
    config_name = input("\n输入创建的配置名称：")

    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "runtime", config_name + '.txt')
    if os.path.exists(config_file):
        if new_cfg:
            print("配置已存在，输入完成后，原来的配置文件将被覆盖！")
        else:
            # read config json
            with open(config_file, 'r', encoding='utf-8') as f:
                runtime_json = json.load(f)
    elif not new_cfg:
        print("配置:%s 不存在，请使用 配置_创建.bat 创建一个新的配置" % config_name)
        exit(1)

    # workspace
    runtime_json['workspace'] = input("\n输入视频所在目录：")

    # video
    if 'video' in runtime_json:
        video_json = runtime_json['video']
    else:
        video_json = {
            "input": "video.mp4",
            "output": "output.mp4",
            "audio": True
        }
    fps = input("\n输入视频帧率(默认15)：")
    if is_empty(fps):
        fps = 15
    else:
        fps = int(fps)
    video_json['fps'] = fps
    runtime_json['video'] = video_json

    # setting
    if 'setting' in runtime_json:
        setting_json = runtime_json['setting']
    else:
        setting_json = dict()

    sd_type = input("\n输入SD类型(默认图生图)：\n0.图生图\n1.文生图\n")
    if is_empty(sd_type) or sd_type == '0':
        sd_type = "img2img"
    else:
        sd_type = "txt2img"
    setting_json["type"] = sd_type

    if new_cfg:
        setting_resize = {}
        resize_mode = input("\n选择图片缩放方式(默认0)：\n0.不缩放\n1.等比缩放\n2.指定宽高\n")
        if is_empty(resize_mode) or (resize_mode != '1' and resize_mode != '2'):
            setting_resize = {"scale": 1.0}
        elif resize_mode == '1':
            scale = input("\n输入图片缩放比例(默认1.0)：")
            setting_resize = {"scale": float(scale)}
        elif resize_mode == '2':
            width = input("\n输入图片宽度：")
            height = input("\n输入图片高度：")
            setting_resize = {
                "width": int(width),
                "height": int(height)
            }
        setting_json["resize"] = setting_resize

        crop_mode = input("\n选择图片裁剪方式(默认1)：\n0.不裁剪\n1.最小化裁剪\n2.等宽高裁剪\n")
        if is_empty(crop_mode):
            crop_mode = 1
        setting_json['crop'] = int(crop_mode)

        setting_json["webui_api_url"] = input("\n输入webui api 地址(默认 http://127.0.0.1:7860/)：")

        seed = input("\n输入种子(默认-1)：\n-1: 随机种子\n1: 第一张图的种子\n指定数字作为种子\n")
        if is_empty(seed):
            seed = -1
        setting_json["seed"] = int(seed)

        inpaint = input("\n是否使用蒙版绘制(默认0)：\n0.不使用\n1.使用\n")
        setting_json["inpaint"] = False if is_empty(inpaint) or inpaint == "0" else True

        mask_mode = input("\n选择抠图算法(默认1)：\n0.不抠图\n1.transparent-background-fast: 速度快，效果一般\n2.transparent-background: 速度慢，效果较好\n3.指定颜色值，只适用于纯色背景(颜色值按需修改)抠图，速度快，效果好\n")
        if is_empty(mask_mode) or mask_mode == "1":
            mask_mode = "transparent-background-fast"
        elif mask_mode == "2":
            mask_mode = "transparent-background"
        elif mask_mode == "3":
            mask_mode = input("\n输入颜色值：(比如#ffffff)\n")
        else:
            mask_mode = ""
        setting_json["mask_mode"] = mask_mode

        mask_bg_mode = input("\n选择背景填充方式(默认1)：\n0.不填充\n1.填充为白色\n2.填充为指定颜色(#RRGGBBAA)\n3.背景透明\n")
        if is_empty(mask_bg_mode) or mask_bg_mode == "1":
            mask_bg_mode = "#ffffff"
        elif mask_bg_mode == "2":
            mask_bg_mode = input("\n输入颜色值：(比如#ffffff)\n")
        elif mask_bg_mode == "3":
            mask_bg_mode = "transparent"
        else:
            mask_bg_mode = ""
        setting_json["mask_bg_mode"] = mask_bg_mode

        tag_json = {}
        tag_mode = input("\n选择反推tag管理模式(默认1)：\n0.不使用反推tag\n1.直接使用生成的tag\n2.只保留动作表情tag\n3.每帧保留动作表情，并提取高频tag作为公共tag\n")
        if is_empty(tag_mode) or tag_mode == "1":
            tag_json = {
                "enable": True,
                "mode": ""
            }
        elif tag_mode == "2":
            tag_json = {
                "enable": True,
                "mode": "action"
            }
            actions = input("\n输入动作表情tag列表，多个tag用逗号分隔(默认:open,opened,close,closed,blink,smile,laugh,behind)：\n")
            if is_empty(actions):
                actions = "open,opened,close,closed,blink,smile,laugh,behind"
            tag_json["actions"] = actions.split(",")
        elif tag_mode == "3":
            tag_json = {
                "enable": True,
                "mode": "action_common"
            }
            actions = input("\n输入动作表情tag列表，多个tag用逗号分隔(默认:open,opened,close,closed,blink,smile,laugh,behind)：\n")
            if is_empty(actions):
                actions = "open,opened,close,closed,blink,smile,laugh,behind"
            tag_json["actions"] = actions.split(",")

        runtime_json['tag'] = tag_json

        overlay = input("\n是否把生成图覆盖回原图(默认1)：\n0.否\n1.是\n")
        if is_empty(overlay) or overlay == "1":
            overlay = True
        else:
            overlay = False
        setting_json["overlay"] = overlay

    runtime_json['setting'] = setting_json

    # webui
    if 'webui' in runtime_json:
        webui_config = runtime_json['webui']
    else:
        webui_config = dict()
    webui_config['prompt'] = input("\n输入sd正向提示词：\n")
    webui_config['negative_prompt'] = input("\n输入sd负向提示词：\n")
    denoising_strength = input("\n输入sd重绘强度(默认0.6)：\n")
    if is_empty(denoising_strength):
        denoising_strength = 0.6
    else:
        denoising_strength = float(denoising_strength)
    webui_config['denoising_strength'] = denoising_strength

    cfg_scale = input("\n输入sd cfg_scale(默认7)：\n")
    if is_empty(cfg_scale):
        cfg_scale = 7
    else:
        cfg_scale = float(cfg_scale)
    webui_config['cfg_scale'] = cfg_scale

    if new_cfg:
        sampler_name = input("\n输入sd采样器（默认:Euler a）：\n")
        if is_empty(sampler_name):
            sampler_name = "Euler a"
        webui_config['sampler_name'] = sampler_name

        steps = input("\n输入sd重绘步数(默认20)：\n")
        if is_empty(steps):
            steps = 20
        else:
            steps = int(steps)
        webui_config['steps'] = steps

    runtime_json['webui'] = webui_config

    ct = input("\n选择 controlnet 组合（默认:0）：\n0.lineart_realistic + tile_colorfix\n1.lineart_realistic + tile_colorfix + temporalnet\n")
    if is_empty(ct) or ct != "1":
        ct = "lineart_tile.txt"
    else:
        ct = "lineart_temporanet_tile.txt"

    runtime_json['config'] = {
        "setting": "img_base.txt",
        "webui": ct
    }

    # write json to file
    with open(config_file, 'w') as f:
        json.dump(runtime_json, f, indent=4)

    print("\n配置文件已生成，请复制文件路径，在 启动_自动模式 或 启动_交互模式 下输入路径来启动工作流。路径：" + config_file)
