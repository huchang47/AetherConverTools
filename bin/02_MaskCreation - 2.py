from transformers import AutoProcessor, CLIPSegForImageSegmentation
from PIL import Image
import glob
import torch
import numpy as np
import os
import cv2
import shutil

print("检测是否有可用的CUDA设备中……")
# 检查是否有可用的CUDA设备
if torch.cuda.is_available():
    device = torch.device("cuda")
    print("加速成功！使用的设备：CUDA")
else:
    device = torch.device("cpu")
    print("加速失败！使用的设备：CPU")


# 定义修改图片大小函数
def resize_img(img, w, h):
    if img.shape[0] + img.shape[1] < h + w:
        interpolation = interpolation = cv2.INTER_CUBIC
    else:
        interpolation = interpolation = cv2.INTER_AREA

    return cv2.resize(img, (w, h), interpolation=interpolation)


def create_mask_clipseg(
    input_dir,
    output_dir,
    clipseg_mask_prompt,
    clipseg_exclude_prompt,
    clipseg_mask_threshold,
    mask_blur_size,
    mask_blur_size2,
):
    processor = AutoProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
    model = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")
    model.to(device)

    imgs = glob.glob(os.path.join(input_dir, "*.png"))
    texts = [x.strip() for x in clipseg_mask_prompt.split(",")]
    exclude_texts = (
        [x.strip() for x in clipseg_exclude_prompt.split(",")]
        if clipseg_exclude_prompt
        else None
    )

    if exclude_texts:
        all_texts = texts + exclude_texts
    else:
        all_texts = texts

    for img_count, img in enumerate(imgs):
        image = Image.open(img)
        base_name = os.path.basename(img)

        inputs = processor(
            text=all_texts,
            images=[image] * len(all_texts),
            padding="max_length",
            return_tensors="pt",
        )
        inputs = inputs.to(device)

        with torch.no_grad():
            outputs = model(**inputs)

        if len(all_texts) == 1:
            preds = outputs.logits.unsqueeze(0)
        else:
            preds = outputs.logits

        mask_img = None

        for i in range(len(all_texts)):
            x = torch.sigmoid(preds[i])
            x = x.to("cpu").detach().numpy()

            #            x[x < clipseg_mask_threshold] = 0
            x = x > clipseg_mask_threshold

            if i < len(texts):
                if mask_img is None:
                    mask_img = x
                else:
                    mask_img = np.maximum(mask_img, x)
            else:
                mask_img[x > 0] = 0

        mask_img = mask_img * 255
        mask_img = mask_img.astype(np.uint8)

        if mask_blur_size > 0:
            mask_blur_size = mask_blur_size // 2 * 2 + 1
            mask_img = cv2.medianBlur(mask_img, mask_blur_size)

        if mask_blur_size2 > 0:
            mask_blur_size2 = mask_blur_size2 // 2 * 2 + 1
            mask_img = cv2.GaussianBlur(mask_img, (mask_blur_size2, mask_blur_size2), 0)

        mask_img = resize_img(mask_img, image.width, image.height)

        mask_img = cv2.cvtColor(mask_img, cv2.COLOR_GRAY2RGB)
        save_path = os.path.join(output_dir, base_name)
        cv2.imwrite(save_path, mask_img)

        print("{0} / {1}".format(img_count + 1, len(imgs)))


# 定义需要处理的视频文件路径
folder_path = os.path.dirname(os.getcwd())

# 定义输出图片和蒙版的目录
frame_out_dir = os.path.join(folder_path, "video_frame")
mask_out_dir = os.path.join(folder_path, "video_mask2")

# 蒙版目录存在就删除
if os.path.exists(mask_out_dir):
    shutil.rmtree(mask_out_dir)
# 创建蒙版输出目录
os.makedirs(mask_out_dir)

create_mask_clipseg(
    frame_out_dir, mask_out_dir, "Girl with headphones,girl in green and blue shirt", "", 0.01, 0, 10
)
