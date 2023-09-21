import base64
import os.path
from io import BytesIO
from math import ceil
from pathlib import Path

import PIL
import numpy as np
from PIL import Image
import cv2
from torchvision import transforms
import torch


# 定义图片转base64函数
def img_encode(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    buffered.close()
    return img_str


def concat_images(images):
    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)
    new_im = Image.new('RGBA', (total_width, max_height))
    x_offset = 0
    for im in images:
        new_im.paste(im, (x_offset, 0))
        x_offset += im.size[0]
    return new_im


def concat_masks(mask, w, h, x, y):
    new_mask = Image.new("RGB", (w, h), "black")
    new_mask.paste(mask, (x, y))
    return new_mask


# 定义智能倍率函数
def get_vam(cur_w, cur_h, tar_size, types):
    ratio_o = cur_w / cur_h
    if types == 1:
        # 长边方案：将长边缩放到该尺寸
        if ratio_o >= 1:  # 横屏
            vam = tar_size / cur_w
        else:  # 竖屏
            vam = tar_size / cur_h
    else:
        # 短边方案：将短边缩小到该尺寸，原本就小的不调整
        min_size = min(cur_w, cur_h, tar_size)
        if min_size == tar_size:
            vam = tar_size / min(cur_w, cur_h)
        else:
            vam = 1
    return vam


# 定义寻找最大区域函数
def max_area(img: cv2.Mat):
    # 使用OpenCV 4.x版本的返回值
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # 使用list()创建一个空列表
    area = list()
    # 使用enumerate()遍历轮廓列表，并同时获取索引和元素
    for i, c in enumerate(contours):
        # 保存计算结果在一个变量中，并复用这个变量
        area_i = cv2.contourArea(c)
        area.append(area_i)
    # 同时获取最大面积的索引和值
    max_idx, max_area = max(enumerate(area), key=lambda x: x[1])

    # 遍历轮廓列表
    for k, c in enumerate(contours):
        # 跳过最大面积的轮廓
        if k == max_idx: continue
        # 绘制非最大面积的轮廓为黑色，并填充其内部区域
        cv2.drawContours(img, contours, k, 0, -1)
    return img


def img_to_mask(img: cv2.Mat):
    gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 二值化
    _, im_g = cv2.threshold(gray_image, 177, 255, cv2.THRESH_BINARY)
    # 将二值化后的图像转换为numpy数组
    im_np = np.array(im_g)
    # 调用max_area函数，获取最大面积的图像
    im = np.zeros_like(im_np)  # 创建与输入图像大小相同的黑色图像
    max_area_mask = max_area(im_np)  # 获取仅包含最大轮廓的掩膜图像
    im[max_area_mask == 255] = 255  # 将输出图像中对应的像素设为白色
    return im


def parse_rgb(color: str):
    """
    convert color str to rgba
    :param color: #rrggbbaa
    :return:
    """
    color = color.replace('#', '')
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return r, g, b


def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    Max = max(r, g, b)
    Min = min(r, g, b)
    D = Max - Min

    HSV = [0, 0, 255]
    HSV[2] = int(Max * 255)
    HSV[1] = int(255 * (D / Max)) if Max != 0 else 0
    if D == 0:
        HSV[0] = 0
    elif Max == r:
        HSV[0] = (60 * ((g - b) / D)) % 360
    elif Max == g:
        HSV[0] = (120 + 60 * ((b - r) / D)) % 360
    elif Max == b:
        HSV[0] = (240 + 60 * ((r - g) / D)) % 360

    HSV[0] = int(HSV[0] / 2)
    return HSV[0], HSV[1], HSV[2]


# 定义一个倍数函数
def round_up(num, mul):
    return (num // mul + 1) * mul


def crop_mask_image(image: PIL.Image, device=None):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    if device is None:
        device = "cpu"
    # 转换图像为Tensor并将其移动到CUDA设备上
    image_tensor = transforms.ToTensor()(image).unsqueeze(0).to(device)

    # 执行裁切操作
    mask = (torch.abs(image_tensor - 1.0) <= 0.5).all(dim=1)
    non_zero_indices = torch.nonzero(mask)
    left = non_zero_indices[:, 2].min().item()
    top = non_zero_indices[:, 1].min().item()
    right = non_zero_indices[:, 2].max().item()
    bottom = non_zero_indices[:, 1].max().item()

    # 左闭右开
    left = int(left)
    top = int(top)
    right = ceil(right) + 1
    bottom = ceil(bottom) + 1

    # 检查裁切点是否有效
    if left >= right or top >= bottom:
        raise Exception("Error：未找到足够的白色像素区域。")

    # 裁切后长宽需要是8的倍数
    frame_w, frame_h = image.size  # 原图长和高
    dw = right - left  # 差值 裁切后图的长
    dh = bottom - top  # 差值 裁切后图的高
    frame_w2 = round_up(dw, 8)  # 长重整为8的倍数
    frame_h2 = round_up(dh, 8)  # 高重整为8的倍数
    dw2 = frame_w2 - dw  # 新长和旧长的差值
    dh2 = frame_h2 - dh  # 新高和旧高的差值
    if left > dw2:  # 如果左侧还有地方
        left = left - dw2  # 差值就加到左边
    elif frame_w - right > dw2:  # 如果右侧还有地方
        right = right + dw2  # 差值就加到右边
    else: # 都不满足，则使用原图
        left = 0
        right = frame_w
    if top > dh2:  # 如果上面还有地方
        top = top - dh2  # 差值就加到上面
    elif frame_h - bottom > dh2:  # 如果下面还有地方
        bottom = bottom + dh2  # 差值就加到下面
    else: # 都不满足，则使用原图
        top = 0
        bottom = frame_h

    # 转换为NumPy数组并裁切图像
    image_array = np.array(image)
    cropped_image = Image.fromarray(image_array[top:bottom, left:right])
    return cropped_image, left, top, right, bottom

