# AetherConverTools - 以太转换工具
- 特别鸣谢[以太之尘丨](https://space.bilibili.com/1689500)，[尽灭](https://github.com/GoldenLoong)，[October](https://github.com/philodoxos)，[浮尘](https://b23.tv/qZusVvg)
- 以太流横版视频转成竖版后重绘，再恢复横版输出视频，全套工作流的辅助工具。
- 配合[ebsynth_utility](https://github.com/s9roll7/ebsynth_utility)使用，可获得更好的效果。

## 环境安装：
1. 安装``Python环境``，版本大于3.10.8。[官方下载页面](https://www.python.org/downloads/)
2. 运行``双击安装必要组件.bat``，安装Python下会用到的组件
3. 安装``FFMpeg``，注意需要将路径添加为系统变量，[官方下载页面](https://github.com/BtbN/FFmpeg-Builds/releases)
4. 生成蒙版和透明时如果报错，请在``C:\Users\你的用户名\.transparent-background``查看是否有2个350m大小的模型文件，理论上他们会自动下载，但会因为网络问题下载不成功。
5. 大部分所需的AI模型文件能够自动下载。但在图生图时想要调用ControlNet需要自行调试好环境，适用于对Stable Diffusion有一定了解的用户。

## 素材准备：
0. 将视频文件命名为``video.mp4``，放在工作流根目录，运行``Stage0_视频转帧(可选).bat``生成帧文件和蒙版文件

## 执行步骤：
1. 运行``01_从头开始工作流.bat``文件，跟随引导完成工作流
2. 可运行``02_中途开始工作流.bat``文件，随时运行任意工作流步骤