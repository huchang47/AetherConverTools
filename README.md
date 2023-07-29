# AetherConverTools - 以太转换工具
- 特别鸣谢[以太之尘丨](https://space.bilibili.com/1689500)，[尽灭](https://github.com/GoldenLoong)，[October](https://github.com/philodoxos)
- 以太流横版视频转成竖版后重绘，再恢复横版输出视频，全套工作流的辅助工具。
- 配合[ebsynth_utility](https://github.com/s9roll7/ebsynth_utility)和[Segment-Anything](https://github.com/continue-revolution/sd-webui-segment-anything)使用，可获得更好的效果。

# 安装
下载项目后，需要`python>=3.8`环境，以及其他一些必要的组件，待后续完善补充。
理论上你可以正常使用`Stable Diffusion`，就没有什么问题。
部分缺少的组件会自动安装。

# 使用
## 素材准备：
1. 用你习惯的方式，生成视频的帧文件（或关键帧），放入名为``video_frame``的文件夹
2. 用你习惯的方式，生成对应帧的蒙版文件，放入``video_mask``
3. 上述两个文件夹内的文件，保证都是png文件，且文件名一一对应

## 执行步骤：
1. 运行``Stage1_横裁竖.bat``文件，等待运行结束（有CUDA会得到加速）,可选择同步反推提示词文件
2. 裁切完成的帧文件在``video_frame_w``，蒙版文件在``video_mask_w``，文件夹会自动生成
3. 运行``Stage2_图生图.bat``，调用Webui的api，将``video_frame_w``中的文件进行图生图，放置在``video_remake``文件夹
4. （可选）使用``StageETC.bat``文件，对图生图结果文件进行各种操作，包括：
	4.1  生成新的蒙版文件，放入mask文件夹
	4.2  生成透明背景图像（需要先运行4.1），放入alpha文件夹
	4.3  将图生图图像与裁切文件进行尺寸对齐（建议优先于其他两步进行），放入upscale文件夹
5. 运行``Stage3_竖进横.bat``文件，``video_remake``文件夹内的图像，融合回``video_frame``的图像中，生成的文件在``video_frame_Done``中

## 可选步骤：
1. 素材准备可通过``Stage0_视频转帧(可选).bat``直接生成，无需借助其他工具
2. 图生图的成品，可在放入``video_remake``目录后，使用``StageETC_辅助功能.bat``对图生图结果文件进行各种操作，包括：
    2.1  生成新的蒙版文件，放入mask文件夹
	2.2  生成透明背景图像（需要先运行4.1），放入alpha文件夹
	2.3  将图生图图像与裁切文件进行尺寸对齐，放入upscale文件夹

## 后续工作：
1. 用你习惯的方式，将``video_frame_Done``中的帧制作为视频
