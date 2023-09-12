@echo off  
pip config set install.trusted-host mirrors.aliyun.com
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install pillow
pip3 install torchvision
pip3 install shutil -i
pip3 install transparent-background
pip3 install transformers
pip3 install numpy
pip3 install pandas
pip3 install onnxruntime
pip3 install opencv-python