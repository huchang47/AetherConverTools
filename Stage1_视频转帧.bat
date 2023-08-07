@echo off
chcp 65001 > nul
cd bin
echo 以太转绘工作流
echo.
echo 将视频转换为连续帧图像 & echo 将视频改名为video.mp4后，放入本目录内。自动创建输出文件夹。
echo.
echo 检测是否有可用的CUDA设备中……
call python 01_VideoFrameExtraction.py

echo 是否开始下一步，输出帧图像蒙版文件？
echo 1. 是 & echo 2. 否
echo.
set/p choice = 请输入选项的数字：

if "%choice%"=="1" goto 02_MaskCreation
if "%choice%"=="2" goto End

:02_MaskCreation
echo 生成蒙版，启动！
call python 02_MaskCreation.py

:End
pause