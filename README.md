# AetherConverTools - 以太转换工具
- 特别鸣谢[以太之尘丨](https://space.bilibili.com/1689500)，[尽灭](https://github.com/GoldenLoong)，[October](https://github.com/philodoxos)，[浮尘](https://b23.tv/qZusVvg)
- 以太流横版视频转成竖版后重绘，再恢复横版输出视频，全套工作流的辅助工具。
- 配合[ebsynth_utility](https://github.com/s9roll7/ebsynth_utility)使用，可获得更好的效果。
## 环境安装：
1. 安装``Python环境``，版本大于3.10.8，注意需要勾选Add Path，若没有勾选，请手动添加Python目录到系统环境变量。[官方下载页面](https://www.python.org/downloads/)
2. 运行``双击安装必要组件.bat``，安装Python下会用到的组件
3. 安装``FFMpeg``，注意需要将路径添加为系统环境变量，[官方下载页面](https://github.com/BtbN/FFmpeg-Builds/releases)
4. 部分步骤在首次运行时需要下载特定的AI模型，有可能需要科学上网，下载成功后，不再需要科学上网（除非模型更新）

## 素材准备：
0. 将视频文件命名为``video.mp4``，放在工作流根目录

## 执行步骤：
1. 运行``01_从头开始工作流.bat``文件，跟随引导完成工作流
2. 可运行``02_中途开始工作流.bat``文件，随时运行任意工作流步骤

## 常见问题解决：
1. 明明是N卡且安装了CUDA，却依然只能调用CPU进行运算：
    - 安装的CUDA不适用于Python的pip环境，运行``双击安装必要组件.bat``，安装适用的，此间需下载2个2.6G的文件。
    - 如若仍未解决，先删除已有的touch，再次运行。
2. Subprocess的相关报错：
    - 没有正确安装FFmpeg导致，请正确安装，并加入系统环境变量。
3. 生成蒙版和透明时如果报错：
    - 请在``C:\Users\你的用户名\.transparent-background``查看是否有2个350m大小的模型文件，理论上他们会自动下载，但会因为网络问题下载不成功。
    - 百度网盘地址：``https://pan.baidu.com/s/1jbzPtVz9F4ZpbI-XbIC1OQ?pwd=atct``，手动下载后放到对应目录内。
4. 图生图时服务器“积极的拒绝”：
    - 没有启用主角Stable-Diffusion
    - 没有启用API调用，秋叶整合包前端有选项勾选即可，其他环境在启动命令行中添加``--api``参数后启动
    - 工作流默认的SD地址是127.0.0.1:7860，如果你做过调整，请前往bin文件夹下修改``05_BatchImg2Img.py``文件中的``url``参数为对应的地址
5. 图生图没有图片输出：
    - 查看SD的控制台窗口，会有对应的报错信息，大部分时候是SD的问题，比如爆显存之类的，请自行排查。