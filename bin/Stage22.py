import requests
import cv2
from base64 import b64encode

import io, base64
from PIL import Image

import numpy as np
import os
import math
import copy

from datetime import datetime

ex_server = "http://127.0.0.1:7860"
ex_url = ex_server + "/sdapi/v1/txt2img"

ex_control_dict = {
    "softedge_pidinet" : "control_v11p_sd15_softedge [a8575a2a]",
    "canny" : "control_v11p_sd15_canny [d14c016b]",
    "openpose_full" : "control_v11p_sd15_openpose [cab727d4]",
    "openpose" : "control_v11p_sd15_openpose [cab727d4]",    
    "depth_midas": "control_v11f1p_sd15_depth [cfd03158]",
    "depth_zoe": "control_v11f1p_sd15_depth [cfd03158]",    
    "lineart_realistic": "control_v11p_sd15_lineart [43d4be0d]",    
    "lineart_anime": "control_v11p_sd15s2_lineart_anime [3825e83e]",        
    "normal_bae": "control_v11p_sd15_normalbae [316696f1]",
    "inpainting_global_harmonious": "controlnet_v11p_sd15_inpaint [ebff9138]",
    "tile_resample": "control_v11f1e_sd15_tile [a371b31b]",
    "tile_colorfix": "control_v11f1e_sd15_tile [a371b31b]",
    "tile_colorfix+sharp": "control_v11f1e_sd15_tile [a371b31b]",    
    "reference_only": "None",
    "reference_adain+attn": "None"
}
dpm_sde_sample = 'DPM++ SDE Karras'
euler_a_sample = 'Euler a'

def encodeImage(image):
    retval, buffer = cv2.imencode('.png', image)
    b64img = b64encode(buffer).decode("utf-8")
    return b64img

def getHMS():
    now = datetime.now()
    return now.strftime("[%H:%M:%S]")


def listModelRequest():
    ex_list_model_url = ex_server + "/sdapi/v1/sd-models"
    resp = requests.get(url=ex_list_model_url).json()
    print(resp)
    return resp

def changeModelRequest(model):
    ex_change_model_url = ex_server + "/sdapi/v1/options"
    body = {
        "sd_model_checkpoint": model,
         "CLIP_stop_at_last_layers": 1,
    }

    r = requests.post(url=ex_change_model_url, json=body)
    print(r.json())


def createCNUnit(model, weight, threshold_a=None, guess=True):
    cn = {
        "module": model,
        "model": ex_control_dict[model],
        "weight": weight,
    }
    if threshold_a is not None:
        cn.update({"threshold_a": threshold_a})
        
    if guess:
        cn.update({"control_mode": "ControlNet is more important"})
    else:
        cn.update({"control_mode": "Balanced"})

    return cn

def updateCNImage(control, image):
     enc_img = encodeImage(image) if image is not None else None
     control.update({'input_image': enc_img})
     return control

def createDummyCNUnit():
    dummy = createCNUnit("canny", 0.0)
    dummy["enabled"] = False
    return dummy

class controlnetRequest:
    def __init__(self, prompt, negative_prompt, img, mask,
                 sample, noise, cfg, steps, controls, seed):
        enc_img = encodeImage(img) if img is not None else None
        enc_mask = encodeImage(mask) if mask is not None else None
        height, width, layers = img.shape if img is not None else (None, None, None)
        
        self.url = ex_url
        self.body = {
#            "init_images": [enc_img],
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "mask": enc_mask,
#            "mask_blur": mask_blur,
#            'inpainting_fill': 0,
            'inpaint_full_res': False,
#            'inpaint_full_res_padding': 1,
#            'inpainting_mask_invert': 1,
            "seed": seed,
            "subseed": -1,
            "subseed_strength": 0,
            "denoising_strength": noise,
            "batch_size": 1,
            "n_iter": 1,
            "steps": steps,
            "cfg_scale": cfg,
            "width": width,
            "height": height,
            "restore_faces": False,
            "tiling": False,
            #"eta": 0,
            "sampler_index": sample,
            #"resize_mode": 'Scale to Fit (Inner Fit)',
            "alwayson_scripts": {
                "controlnet": {
                    "args": []
                }
            }
        }
        
        while len(controls) < 6:
            controls.append(createDummyCNUnit())

        controlnet_units = []
        for controlnet in controls:
            cur_unit = {
#                "image": enc_control_img,
                'mask': None, #mask,
                "module": "canny",
                "model": ex_control_dict["canny"],
                "weight": 0.8,
                "resize_mode": "Just Resize",
                "pixel_perfect": True,
                "enabled": True,
            }
            cur_unit.update(controlnet)
            controlnet_units.append(cur_unit)
        
        self.body["alwayson_scripts"]["controlnet"]["args"] = controlnet_units

    def sendRequest(self):
        r = requests.post(self.url, json=self.body)
        return r.json()
    
    def getImageAndSave(self, img, mask, path, log_json=True, save_guides=False):
        enc_img = encodeImage(img)
        enc_mask = encodeImage(mask) if mask is not None else None
        height, width, layers = img.shape if img is not None else (None, None, None)        
        self.body.update({
            #"init_images": [enc_img],
            "mask": enc_mask,
            "width": width,
            "height": height,    
        })
        
        if log_json:
            print_self_body = copy.deepcopy(self.body)
            if "init_images" in print_self_body:
                del print_self_body["init_images"]
            for cn in print_self_body["alwayson_scripts"]["controlnet"]["args"]:
                if "input_image" in cn:
                    del cn["input_image"]
            print(print_self_body)

        js = self.sendRequest()
        print(getHMS(), "got {} images, save to {}".format(len(js["images"]), path))

        pil_image = Image.open(io.BytesIO(base64.b64decode(js["images"][0])))
        numpy_image = np.array(pil_image)
        
        if save_guides and path is not None:
            for i, img_io in enumerate(js["images"][1:]):
                cur_path = os.path.join(os.path.dirname(path), ("guide%d.png" % i))
                guide_img = Image.open(io.BytesIO(base64.b64decode(img_io)))
                np_guide = np.array(guide_img)
                guide_image = cv2.cvtColor(np_guide, cv2.COLOR_RGB2BGR)
                
                assert cv2.imwrite(cur_path, guide_image)

        # Convert the NumPy array to a cv2 image
        image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

        if path is not None:
            print(path)
            assert cv2.imwrite(path, image)

        return image

def createRequestWithDefault(prompt, negative_prompt, img=None, mask=None,
                 sample=dpm_sde_sample, noise=0.75, cfg=7, steps=20, 
                 controls=[createCNUnit("canny", 0.9)], seed=-1):
    return controlnetRequest(**locals())
