# AetherConverTools - 以太转换工具
- 特别鸣谢[以太之尘丨](https://space.bilibili.com/1689500)，[尽灭](https://github.com/GoldenLoong)，[October](https://github.com/philodoxos)
- 以太流横版视频转成竖版后重绘，再恢复横版输出视频，全套工作流的辅助工具。
- 配合[ebsynth_utility](https://github.com/s9roll7/ebsynth_utility)和[Segment-Anything](https://github.com/continue-revolution/sd-webui-segment-anything)使用，可获得更好的效果。

## 环境安装：
1. 安装``Python环境``，版本大于3.10.8。[官方下载页面](https://www.python.org/downloads/)
2. 运行``双击安装必要组件.bat``，安装Python下会用到的组件
3. 安装``FFMpeg``，注意需要将路径添加为系统变量，[官方下载页面](https://github.com/BtbN/FFmpeg-Builds/releases)
4. 生成蒙版和透明时如果报错，请在``C:\Users\你的用户名\.transparent-background``查看是否有2个350m大小的模型文件，理论上他们会自动下载，但会因为网络问题下载不成功。

## 素材准备：
0. 将视频文件命名为``video.mp4``，放在工作流根目录，运行``Stage0_视频转帧(可选).bat``生成帧文件和蒙版文件
1. （可选）用你习惯的方式，生成视频的帧文件（或关键帧），放入名为``video_frame``的文件夹
2. （可选）用你习惯的方式，生成对应帧的蒙版文件，放入``video_mask``
3. 上述两个文件夹内的文件，保证都是png文件，且文件名一一对应

## 执行步骤：
1. 运行``Stage1_横裁竖.bat``文件，等待运行结束（有CUDA会得到加速）,可选择同步反推提示词文件
2. 裁切完成的帧文件在``video_frame_w``，蒙版文件在``video_mask_w``，文件夹会自动生成
3. 运行``Stage2_图生图.bat``，调用Webui的api，将``video_frame_w``中的文件进行图生图，放置在``video_remake``文件夹
4. 运行``StageETC.bat``，对图生图结果文件进行后续操作，包括：
	4.1  将图生图图像与裁切文件进行尺寸对齐，放入upscale文件夹
	4.2  生成透明背景图像，放入alpha文件夹
5. 运行``Stage3_竖进横.bat``文件，``video_remake``文件夹内的图像，融合回``video_frame``的图像中，生成的文件在``video_frame_Done``中
6. 运行``Stage4_生成视频.bat``文件，将``video_frame_Done``文件夹内的成品图片合成为视频，最终成品为``video_Done.mp4``