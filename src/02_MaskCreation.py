import subprocess
import os
import sys

import shutil
import cv2
import numpy as np

from common_config import *
from image_utils import img_to_mask, parse_rgb, rgb_to_hsv


def transparent_bg(workspace: Workspace, param = None):
    args = ['transparent-background', '--source', workspace.input, '--dest', workspace.input_mask, '--type', 'map']
    if not is_empty(param):
        args.append(param)
    subprocess.check_call(args)

    # 开始修正蒙版名称
    files = sorted(os.listdir(workspace.input_mask))
    # 遍历文件列表
    for filename in files:
        if filename.lower().endswith('.png'):
            file_path = os.path.join(workspace.input_mask, filename)
            if '_' in filename:
                name_arr = filename.split('_')
                new_name = f'{name_arr[0]}.png'
                new_file_path = os.path.join(workspace.input_mask, new_name)
                # 重命名文件
                os.rename(file_path, new_file_path)
            else:
                new_name = filename
                new_file_path = os.path.join(workspace.input_mask, new_name)

            # create mask
            img = cv2.imread(new_file_path)
            img = img_to_mask(img)
            cv2.imwrite(new_file_path, img)


# hsv 抠图
def pure_bg2(workspace: Workspace, color):
    r, g, b = parse_rgb(color)
    h, s, v = rgb_to_hsv(r, g, b)
    # HSV 的下界限
    lower = np.array([h - 3, 70, 70])
    # HSV 的上界限
    upper = np.array([h + 3, 255, 255])
    # 腐蚀和膨胀的核
    kernel = np.array([[1, 1, 1], [1, 1, 1], [1, 1, 1]], dtype=np.uint8)

    files = sorted(os.listdir(workspace.input))
    # 遍历文件列表
    for filename in files:
        if filename.lower().endswith('.png'):
            # create mask
            img = cv2.imread(os.path.join(workspace.input, filename))
            img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # 找到H分量在这个范围的区域
            mask = cv2.inRange(img_hsv, lower, upper)
            # 腐蚀图像
            eroded = cv2.erode(mask, kernel, iterations=1)
            # 膨胀图像
            dilated = cv2.dilate(eroded, kernel, iterations=1)
            # 背景颜色改为黑色，前景改成白色
            img[dilated == 255] = [0, 0, 0]
            img[dilated != 255] = [255, 255, 255]
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # 保存蒙版
            cv2.imwrite(os.path.join(workspace.input_mask, filename), img)


# rgb 精确抠图
def pure_bg(workspace: Workspace, color):
    r, g, b = parse_rgb(color)
    files = sorted(os.listdir(workspace.input))
    # 遍历文件列表
    for filename in files:
        if filename.lower().endswith('.png'):
            # create mask
            img = cv2.imread(os.path.join(workspace.input, filename))
            # create a same size gray img by cv2
            img_gray = np.full(img.shape[:2], 255, np.uint8)
            # img_gray = img bgr 相同的部分改成黑色
            img_gray[(img[:, :, 0] == b) & (img[:, :, 1] == g) & (img[:, :, 2] == r)] = 0
            # 保存灰度图
            # create cv image from np array
            # 保存蒙版
            cv2.imwrite(os.path.join(workspace.input_mask, filename), img_gray)



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

    # 蒙版目录存在就删除
    if os.path.exists(workspace.input_mask):
        shutil.rmtree(workspace.input_mask)
    # 创建蒙版输出目录
    os.makedirs(workspace.input_mask)

    # 蒙版算法
    mask_mode = setting_config.get_mask_mode()
    if mask_mode == MASK_MODE_TRANSPARENT_BACKGROUND:
        transparent_bg(workspace)
        print("蒙版文件生成完成！")
    elif mask_mode == MASK_MODE_TRANSPARENT_BACKGROUND_FAST:
        transparent_bg(workspace, '--fast')
        print("蒙版文件生成完成！")
    elif mask_mode[0] == '#': # pure mode
        pure_bg2(workspace, mask_mode)
        print("蒙版文件生成完成！")
    elif mask_mode == MASK_MODE_NONE:
        print("跳过蒙版生成")
        # 强制设置裁剪为false
        setting_config.set_crop_mode(0)
    else:
        print("Error: unknown mask mode")
        exit(ERROR_UNKNOWN_MASK_MODE)

    if it_mode is None:
        it_mode = setting_config.get_interactive_mode()
    if it_mode == INTERACTIVE_MODE_INPUT:
        # 是否进行下一步
        choice = input("\n是否直接开始下一步，把视频帧和蒙版进行裁切？\n1. 是\n2. 否\n请输入你的选择：")
        if choice != "1":
            exit(0)

    subprocess.run(['python', '03_CropImage.py', sys.argv[1]])
