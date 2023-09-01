@echo off  
chcp 65001 > nul  
pip config set install.trusted-host mirrors.aliyun.com
echo.
echo ==============================安装torch和torchvision===============================
echo.
echo 这里会提示你是否要删除CUDA重新安装，如果你的GPU调用没有问题，请输入n，不要卸载重装。
echo 否则会重新下载5.2G的数据，谨慎操作。不影响其他组件的安装。
echo.
echo ===================================================================================
pip3 uninstall torch
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install pillow
pip3 install torchvision
pip3 install shutil -i
pip3 install transparent-background
pip3 install transformers
pip3 install numpy
pip3 install pandas
pip3 install onnxruntime