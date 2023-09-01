@echo off  
chcp 65001 > nul  
echo 即将开始以太转绘工作流，请确保当前目录下有视频文件，且文件名格式为：video.mp4
echo 如果在运行中程序出现错误，极大可能是缺少组件和自动下载模型不成功
echo 请安装组件和科学上网后再次尝试。还有问题，请加群792358210敲打作者
echo.
cd bin
python 01_VideoFrameExtraction.py
pause