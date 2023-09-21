import os

import torch


def prefer_device():
    # 设置Torch不使用图形界面显示
    os.environ["PYTORCH_JIT"] = "1"

    # 检查是否有可用的CUDA设备
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print("使用的设备:CUDA")

        # 使用CUDA进行加速
        torch.set_grad_enabled(False)
    else:
        device = torch.device("cpu")
        print("使用的设备:CPU")

    return device
