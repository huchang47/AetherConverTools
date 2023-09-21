import copy
import shutil
import sys

import io
import base64
import subprocess
from pathlib import Path
from PIL import Image, PngImagePlugin

from common_config import *
from image_utils import img_encode, concat_images, concat_masks


def transform(webui_config: WebuiConfig, setting_config: SettingConfig, workspace: Workspace,
              frame_name: str, ref_transformed_scale: [], ref_transformed: [], ref_masks: []):
    crop = setting_config.enable_crop()
    inpaint = setting_config.enable_inpaint()
    tag = setting_config.enable_tag()

    output_dir = workspace.output_crop if crop else workspace.output
    frame_file = os.path.join(workspace.input_crop if crop else workspace.input, frame_name)
    mask_file = os.path.join(workspace.input_crop_mask if crop else workspace.input_mask, frame_name)
    tag_file = os.path.join(workspace.input_tag, Path(frame_name).stem + ".txt")
    common_tag_file = os.path.join(workspace.input_tag, "common.txt")

    # read image
    cur_img_ori = Image.open(frame_file)
    cur_w, cur_h = cur_img_ori.size

    # control net 上帧参考图
    ct_ref_img_str = None
    # 保存单张图原始大小
    single_w = cur_w
    single_h = cur_h

    ct_ref_img_str = img_encode(ref_transformed_scale[0]) if len(ref_transformed_scale) > 0 else None

    # input img encode
    cur_img_ori_str = img_encode(cur_img_ori)
    cur_img_ori.close()

    # read mask
    cur_mask_ori_str = None
    cur_mask_ref = None
    if inpaint:
        if not os.path.exists(mask_file):
            cur_mask_ori = None
            print("[warning] frame %d: mask not found", frame_name)
        else:
            cur_mask_ori = Image.open(mask_file)
            # 复制原始 mask (cur_mask_ref) 用做下一帧的参考图
            cur_mask_ref = cur_mask_ori.copy()

        # input mask encode
        if cur_mask_ori is not None:
            cur_mask_ori_str = img_encode(cur_mask_ori)
            cur_mask_ori.close()

    # read tag
    if tag:
        if not os.path.exists(tag_file):
            tag_str = None
            print("[warning] frame %d: tag not found", frame_name)
        else:
            with open(tag_file, 'r', encoding="utf-8") as t:
                tag_str = t.read()
        if setting_config.get_tag_mode() == TAG_MODE_ACTION_COMMON:
            if os.path.exists(common_tag_file):
                with open(common_tag_file, 'r', encoding="utf-8") as t:
                    common_tag_str = t.read()
                if not is_empty(common_tag_str):
                    if not is_empty(tag_str):
                        tag_str = tag_str + "," + common_tag_str
                    else:
                        tag_str = common_tag_str

        # 拼接 tag 到 prompt
        if not is_empty(tag_str):
            prompt = webui_config.get_prompt()
            if is_empty(prompt):
                prompt = tag_str
            else:
                prompt = tag_str + "," + prompt
            # 写回到配置
            webui_config.set_prompt(prompt)

    # inflate control net
    webui_config.inflate_control_nets(None if setting_config.is_img2img() else cur_img_ori_str, ct_ref_img_str)

    # 缩放
    scale_w, scale_h, sw, sh = setting_config.get_size_scale(cur_w, cur_h)
    # inflate webui config
    single_scale_w = scale_w if cur_w == single_w else int(single_w * sw)
    single_scale_h = scale_h if cur_h == single_h else int(single_h * sh)

    webui_config.inflate_base(cur_img_ori_str if setting_config.is_img2img() else None, scale_w, scale_h, setting_config.get_current_seed())

    # inflate mask
    if cur_mask_ori_str is not None:
        webui_config.inflate_mask(cur_mask_ori_str)

    print(frame_name + ":开始生成！生成尺寸 " + str(scale_w) + "x" + str(scale_h) + "px")

    response = webui_config.call(setting_config.get_webui_api())
    try:
        response = response.json()
        cur_img_tra_scale = Image.open(io.BytesIO(base64.b64decode(response['images'][0].split(",", 1)[0])))
        # 保存 ct 图，用于调试程序
        # cur_img_ct1 = Image.open(io.BytesIO(base64.b64decode(response['images'][1].split(",", 1)[0])))
        # cur_img_ct1.save(os.path.join(output_dir, "ct1_" + frame_name))
        # cur_img_ct1.close()
        # cur_img_ct2 = Image.open(io.BytesIO(base64.b64decode(response['images'][2].split(",", 1)[0])))
        # cur_img_ct2.save(os.path.join(output_dir, "ct2_" + frame_name))
        # cur_img_ct2.close()
        # if len(response['images']) > 3:
        #     cur_img_ct3 = Image.open(io.BytesIO(base64.b64decode(response['images'][3].split(",", 1)[0])))
        #     cur_img_ct3.save(os.path.join(output_dir, "ct3_" + frame_name))
        #     cur_img_ct3.close()

        # 放大渲染后，重新缩放回原大小
        if cur_img_tra_scale.size[0] != cur_w or cur_img_tra_scale.size[1] != cur_h:
            print("%s:生成图片缩放回原大小" % frame_name)
            cur_img_tra = cur_img_tra_scale.resize((cur_w, cur_h), Image.BICUBIC)
        else:
            cur_img_tra = cur_img_tra_scale.copy()


        # 更新参考图
        if len(ref_transformed) == 0:
            ref_transformed.append(cur_img_tra.copy())
        else:
            ref_transformed[0].close()
            ref_transformed[0] = cur_img_tra.copy()

        if len(ref_transformed_scale) == 0:
            ref_transformed_scale.append(cur_img_tra_scale.copy())
        else:
            ref_transformed_scale[0].close()
            ref_transformed_scale[0] = cur_img_tra_scale.copy()

        if cur_mask_ref is not None:
            if len(ref_masks) == 0:
                ref_masks.append(cur_mask_ref)
            else:
                ref_masks[0].close()
                ref_masks[0] = cur_mask_ref

        # save img
        info = response['info']
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("Parameters: ", info)
        cur_img_tra.save(os.path.join(output_dir, frame_name), pnginfo=pnginfo)
        cur_img_tra.close()
        cur_img_tra_scale.close()

        # 固定种子
        if setting_config.fix_first_seed():
            info = json.loads(info)
            seed = info['seed']
            setting_config.set_seed(seed)
            print("使用第一张图的种子:", seed)

        print(frame_name + "生成完毕！")

        return response
    except Exception as e:
        print(e)
        del response['images']
        if 'parameters' in response:
            params = response['parameters']
            if 'alwayson_scripts' in params:
                alwayson_scripts = params['alwayson_scripts']
                if 'controlnet' in alwayson_scripts:
                    ct_args = alwayson_scripts['controlnet']['args']
                    for ct_arg in ct_args:
                        del ct_arg['input_image']
        print(response)
        exit(ERROR_WEBUI_CALL)


def get_input_frames(setting_config: SettingConfig, workspace: Workspace):
    crop = setting_config.enable_crop()
    frame_names = [f for f in os.listdir(workspace.input_crop if crop else workspace.input) if f.endswith('.png')]
    frame_names.sort()
    return frame_names


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Params: <runtime-config.json>")
        exit(ERROR_PARAM_COUNT)

    it_mode = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        webui_json, setting_json = read_config(sys.argv[1])
    except Exception as e:
        print("Error: read config", e)
        exit(ERROR_READ_CONFIG)

    setting_config = SettingConfig(setting_json)

    # 检查配置
    webui_api = setting_config.get_webui_api()
    if is_empty(webui_api):
        exit(ERROR_WEBUI_API)

    # workspace path config
    workspace = setting_config.get_workspace_config()

    input_frame_names = get_input_frames(setting_config, workspace)
    if len(input_frame_names) == 0:
        print("Error: no input frames")
        exit(ERROR_INPUT_EMPTY)

    output_dir = workspace.output_crop if setting_config.enable_crop() else workspace.output
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # 生成图片-带缩放
    ref_transformed_scale = []
    # 生成图片-输入尺寸
    ref_transformed = []
    ref_masks = []

    for frame_name in input_frame_names:
        # 拷贝一份webui config，每帧的配置有所不同
        transform(WebuiConfig(copy.deepcopy(webui_json)), setting_config, workspace, frame_name, ref_transformed_scale,
                  ref_transformed, ref_masks)

    for img in ref_transformed:
        img.close()
    for img in ref_transformed:
        img.close()
    for img in ref_masks:
        img.close()

    print("全部图片生成完毕！共计" + str(len(input_frame_names)) + "张！")

    if it_mode is None:
        it_mode = setting_config.get_interactive_mode()
    if it_mode == INTERACTIVE_MODE_INPUT:
        # 是否进行下一步
        choice = input("\n是否直接开始下一步，将图生图后的图像与裁切图片进行尺寸对齐？\n1. 是\n2. 否\n请输入你的选择：")
        if choice != "1":
            exit(0)
    subprocess.run(['python', '06_OverlayImage.py', sys.argv[1]])
