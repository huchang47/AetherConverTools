import os
import shutil
import sys
import subprocess
import glob
from PIL import Image

from common_config import *


def blend(output_path:str, src_path:str, blend_path:str, mask_path:str, x:int, y:int):
    src = Image.open(src_path).convert("RGBA") # 打开原图
    overlay = Image.open(blend_path).convert("RGBA")  # 打开新图
    mask = Image.open(mask_path).convert("L")  # 打开新图
    # 蒙版抠图
    overlay.putalpha(mask)
    # 还原到原图
    src.paste(overlay, (x, y), mask=overlay)   # 贴进去
    src.save(output_path) # 保存
    src.close()
    overlay.close()
    mask.close()


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

    setting_config = SettingConfig(setting_json)

    # workspace path config
    workspace = setting_config.get_workspace_config()

    # 输出目录存在就删除
    if os.path.exists(workspace.output):
        shutil.rmtree(workspace.output)
    os.makedirs(workspace.output)

    # 可选功能
    if setting_config.enable_overlay():
        if setting_config.enable_crop():
            # crop 图覆盖回原图
            # 遍历坐标文件
            with open(workspace.crop_info, 'r') as info_file:
                crop_info = info_file.readlines()

            files = [f for f in os.listdir(workspace.output_crop) if f.endswith('.png')]
            files.sort()
            for file_name, info in zip(files, crop_info):
                _, left, top, right, bottom = map(str, info.split(','))  # 读取坐标

                src_path = os.path.join(workspace.input, file_name)
                blend_path = os.path.join(workspace.output_crop, file_name)
                mask_path = os.path.join(workspace.input_crop_mask, file_name)
                output_path = os.path.join(workspace.output, file_name)
                blend(output_path, src_path, blend_path, mask_path, int(left), int(top))
            print("还原图成功")
        elif setting_config.get_mask_bg_mode() != MASK_BG_MODE_NONE:
            # 替换背景后 蒙版覆盖回原图
            files = [f for f in os.listdir(workspace.output) if f.endswith('.png')]
            files.sort()
            for file_name in files:
                src_path = os.path.join(workspace.input, file_name)
                blend_path = os.path.join(workspace.output, file_name)
                mask_path = os.path.join(workspace.input_mask, file_name)
                output_path = os.path.join(workspace.output, file_name)
                blend(output_path, src_path, blend_path, mask_path, 0, 0)
            print("还原图成功")

    if it_mode is None:
        it_mode = setting_config.get_interactive_mode()
    if it_mode == INTERACTIVE_MODE_INPUT:
        # 是否进行下一步
        choice = input("\n是否直接开始下一步，将融合完成的图片生成视频？\n1. 是\n2. 否\n请输入你的选择：")
        if choice != "1":
            exit(0)
    subprocess.run(['python', '07_Img2Video.py', sys.argv[1]])
