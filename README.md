# AetherConverTools - 以太转换工具
- 特别鸣谢[以太之尘丨](https://space.bilibili.com/1689500)，[尽灭](https://github.com/GoldenLoong)，[October](https://github.com/philodoxos)，[浮尘](https://b23.tv/qZusVvg)，[阿珂](https://github.com/ItTianYuStudio)
- 以太流横版视频转成竖版后重绘，再恢复横版输出视频，全套工作流的辅助工具。
- 配合[ebsynth_utility](https://github.com/s9roll7/ebsynth_utility)使用，可获得更好的效果。
## 环境安装：
1. 安装``Python环境``，版本大于3.10.8，注意需要勾选Add Path，若没有勾选，请手动添加Python目录到系统环境变量。[官方下载页面](https://www.python.org/downloads/)
2. 运行``双击安装必要组件.bat``，安装Python下会用到的组件
3. 安装``FFMpeg``，注意需要将路径添加为系统环境变量，[官方下载页面](https://github.com/BtbN/FFmpeg-Builds/releases)
4. 部分步骤在首次运行时需要下载特定的AI模型，有可能需要科学上网，下载成功后，不再需要科学上网（除非模型更新）

## 素材准备：
1. 将视频文件命名为`video.mp4`，放在任意目录下，复制此目录的路径
2. 修改一个配置，比如 `config/runtime/sample_img_base.txt` 文件中的`workspace`参数为刚才复制的目录路径

## 执行步骤：
- 运行`启动_自动模式.bat` 或 `启动_交互模式.bat`文件;
- 选择开始的步骤，比如 1;
- 输入 `config/runtime` 下的任意配置文件路径（可直接拖拽配置文件到命令行）。比如 `D:/AetherConverTools/config/runtime/sample_img_base.txt`;

## 样例配置

- runtime
  - sample_img_base.txt: 图生图 基础配置
    - controlnet: lineart:0.6 + tile:0.6
    - 缩放: 1.0
    - 重绘强度: 0.6
    - 裁剪: 最小化
    - inpaint: 关
  - sample_img_tag_tem.txt: 图生图 基础 + tem loopback
    - controlnet: lineart:0.6 + tile:0.6 + tem:0.6
  - sample_txt_base.txt: 文生图 基础配置
  - sample_txt_tag_tem.txt: 文生图 基础 + tem loopback


## runtime 配置

运行依赖的相关配置

提示：如果不会修改，请使用样例里的配置

- workspace: 工作目录，存放输入输出和临时文件

- video: 输入视频配置
  - input: 输入视频文件名
  - output: 输出视频文件名
  - fps: 提取的视频帧率
  - audio: 是否提取视频音频

- webui:
  - denoising_strength: 重绘强度
  - prompt: 正向提示词
  - negative_prompt: 负向提示词
  - sampler_name: 采样器
  - steps: 重绘步数

- config:
  - setting: 使用的 setting 配置文件路径
  - webui: 使用的 webui 配置文件路径

## setting 配置：

工作流相关配置

提示：如果不会修改，请使用样例里的配置

- type:
  - img2img: 图生图
  - txt2img: 文生图

- seed:
  - -1: 随机
  - 1: 使用第一张图的种子
  - xxxxx: 自定义种子

- mask_mode: 蒙版抠图算法
  - transparent-background-fast: 速度快，效果一般
  - transparent-background: 速度慢，效果较好
  - #RRGGBBAA: 只适用于纯色背景(颜色值按需修改)抠图，速度快，效果好
  - sam(暂未支持): segment every thing 抠图，适用于复杂场景，多人多物体。

- mask_bg_mode: 蒙版背景模式
  - "": 不处理背景
  - #RRGGBBAA: 替换为纯色背景(颜色值按需修改)
  - transparent: 替换为透明背景

- tag
  - enable: 是否启用tag反推
  - mode: 反推 tag 管理模式
    - "": 不处理tag
    - action: 单帧只保留动作表情
    - action_common: 提取公共tag, 单帧只保留动作表情
  - actions: 动作表情tag列表，在此列表的 tag 会被当做 动作表情 处理

- crop:
  - 0: 不裁剪
  - 1: 蒙版最小化裁剪
  - 2: 蒙版等尺寸裁剪

- resize: 缩放配置（scale 和 width height字段同时存在情况下，width height 优先级更高）
  - width: 缩放到指定宽，不写忽略
  - height: 缩放到指定高，不写忽略
  - scale: 等比缩放比例，比如 1.5，默认 1

- inpaint: 是否启用蒙版绘制

## webui 配置

webui 相关配置，有能力的自行修改。
可增加或删除 controlnet 模型



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