import math
import os
import sys

import numpy as np
import shutil
import subprocess
import glob
from PIL import Image

from common_utils import prefer_device
from common_config import *
from image_utils import crop_mask_image, parse_rgb


def join_list(l: [], sep: str) -> str:
    return sep.join([item if isinstance(item, str) else str(item) for item in l])


def crop_info_to_str(crop_info: []) -> str:
    return "\n".join([join_list(item, ",") for item in crop_info])


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

    # 不存在就创建
    if not os.path.exists(workspace.input_crop_mask):
        os.makedirs(workspace.input_crop_mask)

    # 检查是否存在原始坐标文件，如果存在则删除
    if os.path.exists(workspace.crop_info):
        os.remove(workspace.crop_info)

    # 可选功能
    if setting_config.enable_crop():

        # 遍历蒙版文件夹下的所有PNG图片
        width = 0
        height = 0

        mask_files = [f for f in os.listdir(workspace.input_mask) if f.endswith('.png')]
        mask_files.sort()
        crop_info = []
        for file_name in mask_files:
            file_path = os.path.join(workspace.input_mask, file_name)
            output_path = os.path.join(workspace.input_crop_mask, file_name)
            img = Image.open(file_path)
            width, height = img.size

            try:
                cropped_img, left, top, right, bottom = crop_mask_image(img, device)
                crop_info.append((file_name, left, top, right, bottom))
                # save cropped image
                cropped_img.save(output_path)
                cropped_img.close()
                print(f"{file_name} 蒙版裁切完毕，裁切点：({left},{top}), ({right},{bottom})")
            except Exception as e:
                print(str(e))
                # crop_info.append((file_name, 0, 0, 0, 0))
                continue
            finally:
                img.close()


        # write crop info
        with open(workspace.crop_info, "w") as f:
            f.write(crop_info_to_str(crop_info))

        if setting_config.get_crop_mode() == CROP_MODE_ACCORDANT:
            max_crop_w = 0
            max_crop_h = 0

            diff_info = []
            for item in crop_info:
                filename, x1, y1, x2, y2 = item
                crop_w = x2 - x1
                crop_h = y2 - y1
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                if crop_w > max_crop_w:
                    max_crop_w = crop_w
                if crop_h > max_crop_h:
                    max_crop_h = crop_h

                diff_info.append((filename, crop_w, crop_h, center_x, center_y))

            max_crop_w = round_up(max_crop_w, 8)
            max_crop_h = round_up(max_crop_h, 8)
            if max_crop_w > width:
                max_crop_w = width
            if max_crop_h > height:
                max_crop_h = height

            max_crop_w_half = max_crop_w // 2
            max_crop_h_half = max_crop_h // 2

            new_info = []
            for item in diff_info:
                filename, crop_w, crop_h, center_x, center_y = item
                x1 = center_x - max_crop_w_half
                y1 = center_y - max_crop_h_half
                x2 = center_x + max_crop_w_half
                y2 = center_y + max_crop_h_half

                if x1 < 0:
                    p = -x1
                    x1 = x1 + p
                    x2 = x2 + p
                if x2 > width:
                    p = x2 - width
                    x2 = x2 - p
                    x1 = x1 - p

                if y1 < 0:
                    q = -y1
                    y1 = y1 + q
                    y2 = y2 + q
                if y2 > height:
                    q = y2 - height
                    y2 = y2 - q
                    y1 = y1 - q

                new_info.append((filename, x1, y1, x2, y2))


            # crop mask by new info
            for info, diff in zip(new_info, diff_info):
                file, left, top, right, bottom = info
                _, crop_w, crop_h, center_x, center_y = diff
                if crop_w == right - left and crop_h == bottom - top:
                    continue
                img = Image.open(os.path.join(workspace.input_mask, file))
                cropped_img = img.crop((left, top, right, bottom))
                cropped_img.save(os.path.join(workspace.input_crop_mask, file))
                cropped_img.close()
                img.close()
                print(f"{file} 蒙版重新裁切完毕，裁切点：({left},{top}), ({right},{bottom})")


            # write new crop info
            with open(workspace.crop_info, "w") as f:
                f.write(crop_info_to_str(new_info))

            # replace crop info
            crop_info = new_info


        # clear cache
        if os.path.exists(workspace.input_crop):
            shutil.rmtree(workspace.input_crop)
        os.makedirs(workspace.input_crop)

        # 开始裁切视频帧
        for info in crop_info:
            file, left, top, right, bottom = info
            img = Image.open(os.path.join(workspace.input, file))
            cropped_img = img.crop((left, top, right, bottom))
            cropped_img.save(os.path.join(workspace.input_crop, file))
            cropped_img.close()
            img.close()
            print("帧" + file + "裁切完成！")

        # 获取图像和蒙版文件列表并进行排序
        mask_bg_mode = setting_config.get_mask_bg_mode()
        if mask_bg_mode != MASK_BG_MODE_NONE:
            if mask_bg_mode[0] == '#':
                r, g, b = parse_rgb(mask_bg_mode)
                bg_color = (r, g, b, 255)
            else:  # transparent
                bg_color = (0, 0, 0, 0)

            # 背景替换
            for file in mask_files:
                if file.endswith(".png"):
                    image_file = os.path.join(workspace.input_crop, file)
                    mask_file = os.path.join(workspace.input_crop_mask, file)
                    image_out_file = os.path.join(workspace.input_crop, file)

                    # 打开图像和蒙版文件
                    with Image.open(image_file) as img, Image.open(mask_file).convert("L") as mask:
                        # 创建纯色背景
                        img_bg = Image.new("RGBA", img.size, bg_color)
                        # 反向蒙版
                        inverted_mask = Image.eval(mask, lambda px: 255 - px)
                        # 将反向蒙版作为蒙版应用到图像上
                        img.paste(img_bg, (0, 0), inverted_mask)
                        # 保存图片
                        img.save(image_out_file, "PNG")
                        img_bg.close()
                    print(file + " 背景替换完成")

    if it_mode is None:
        it_mode = setting_config.get_interactive_mode()
    if it_mode == INTERACTIVE_MODE_INPUT:
        # 是否进行下一步
        choice = input("\n是否直接开始下一步，反推提示词？\n1. 是\n2. 否\n请输入你的选择：")
        if choice != "1":
            exit(0)

    subprocess.run(['python', '04_GeneratePrompt.py', sys.argv[1]])
