import os
import sys
import shutil
from pathlib import Path

from PIL import Image
import subprocess

from common_config import *


# 定义偶数尺寸函数
def even_size(img_size):
    if img_size % 2 != 0:
        img_size += 1
    return int(img_size)


# 定义提取音频函数
def extract_music_from_video(video_file, music_file):
    # 调用FFmpeg从视频中提取音频
    subprocess.call(['ffmpeg', '-y', '-i', video_file, '-q:a', '0', '-map', 'a', '-c:a', 'aac', music_file])


# 定义合成视频函数
def convert_images_to_video(image_path, output_file, fps, bit_rate):
    # 调用FFmpeg将图片合成为视频
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps), "-i", os.path.join(image_path, '%05d.png'),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), '-b:v', bit_rate, output_file
    ])


def attach_music(output_file, video_file, music_file):
    # 调用FFmpeg将音乐合成进视频
    subprocess.call(
        ['ffmpeg', '-i', video_file, '-i', music_file, '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0',
         '-map', '1:a:0', '-y', output_file])


def get_bit_rate(video_file):
    json_str = subprocess.check_output(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_entries", "stream=bit_rate", video_file])
    info = json.loads(json_str)
    return info["streams"][0]["bit_rate"]


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Params: <runtime-config.json>")
        exit(ERROR_PARAM_COUNT)

    it_mode = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        setting_json = read_config(sys.argv[1], webui=False)
    except Exception as e:
        print("Error: read config", e)
        exit(ERROR_READ_CONFIG)

    setting_config = SettingConfig(setting_json)

    # workspace path config
    workspace = setting_config.get_workspace_config()

    video_config = setting_config.get_video()
    input_file = os.path.join(workspace.root, video_config.get_input())
    output_file = os.path.join(workspace.root, video_config.get_output())
    fps = video_config.get_fps()

    if video_config.enable_audio():
        output_path = Path(output_file)
        silent_file = os.path.join(output_path.parent, output_path.stem + "_silent" + output_path.suffix)
        music_file = os.path.join(output_path.parent, output_path.stem + ".m4a")  # 提取视频音乐文件
        if os.path.exists(music_file):
            os.remove(music_file)
    else:
        silent_file = output_file
        music_file = None

    # 删除缓存
    if os.path.exists(silent_file):
        os.remove(silent_file)

    # 输出最终视频文件
    bit_rate = get_bit_rate(input_file)
    convert_images_to_video(workspace.output, silent_file, fps, bit_rate)

    if video_config.enable_audio():
        # 删除缓存
        if os.path.exists(output_file):
            os.remove(output_file)

        # 提取原视频音频文件
        extract_music_from_video(input_file, music_file)
        # 合成视频附加音乐
        attach_music(output_file, silent_file, music_file)
        os.remove(music_file)

    print("\n视频文件生成完毕！")
