import os
import shutil
from PIL import Image
import subprocess


# 获取当前文件夹路径
folder_path = os.path.dirname(os.getcwd())
frame_path = os.path.join(folder_path, "video_frame_Done")  # 定义图像成品文件夹
frame_tmp_path = os.path.join(folder_path, "video_frame_tmp")   # 图片临时文件夹

# 如果output_folder不存在，则创建它
if not os.path.exists(frame_tmp_path):
    os.makedirs(frame_tmp_path)

# 定义文件路径
video_filename = os.path.join(folder_path, "video.mp4") # 原始视频文件
music_filename = os.path.join(folder_path, "video.mp3") # 提取视频音乐文件
video_tmp_filename = os.path.join(folder_path, "video_tmp.mp4") # 无音乐的新视频文件
video_out_filename = os.path.join(folder_path, "video_Done.mp4")    # 最终成品

# 定义偶数尺寸函数
def even_size(img_size):
    if img_size %2 != 0:
        img_size += 1
    return int(img_size)

# 定义提取音频函数
def extract_music_from_video(video_file, music_file):
    # 调用FFmpeg从视频中提取音频
    subprocess.call(['ffmpeg', '-y', '-i', video_file, '-q:a', '0', '-map', 'a', music_file])

# 定义合成视频函数
def convert_images_to_video(image_folder, output_video, music_file):

    # 构建图片文件列表
    frame_files = [os.path.join(image_folder, file) for file in os.listdir(image_folder) if file.endswith('.png')]
    frame_files.sort()

    # 图片文件名批量改名
    for i, png_file in enumerate(frame_files):
        new_name = f"{i+1:06d}.png"
        shutil.copy(os.path.join(frame_path, png_file), os.path.join(frame_tmp_path, new_name))

    if frame_files:
        # 获取第一张图的路径
        first_frame_path = os.path.join(image_folder, frame_files[0])

        # 打开第一张图片并获取宽度和高度
        with Image.open(first_frame_path) as img:
            image_width, image_height = img.size

            # 显示第一张图片的宽度和高度
            image_width = even_size(image_width)
            image_height = even_size(image_height)
            print(f"视频输出尺寸={image_width}x{image_height}")
            
        # 调用FFmpeg将图片合成为视频
        subprocess.run([
            "ffmpeg", "-y", "-framerate", str(fps), "-i",
            os.path.join(frame_tmp_path, '%06d.png'), "-c:v", "libx264", "-crf", "0",
            "-r", str(fps),"-s",f"{image_width}x{image_height}", video_tmp_filename
        ])
        # 调用FFmpeg将音乐合成进视频
        subprocess.call(['ffmpeg', '-i', video_tmp_filename, '-i', music_file, '-c:v', 'copy', '-c:a', 'mp3', '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_video])

# 输出原视频音频文件
extract_music_from_video(video_filename,music_filename)

# 输出最终视频文件
fps = input("请输入想要输出的视频帧率（默认15）：") or 15   # 定义fps，默认15帧/秒
convert_images_to_video(frame_path,video_out_filename,music_filename)
os.remove(music_filename)
os.remove(video_tmp_filename)
shutil.rmtree(frame_tmp_path)
print("\n视频文件生成完毕！以太转绘工作流圆满完成！ ✿✿ヽ(°▽ °)ノ✿\n如果你在使用中遇到问题，请加QQ群：792358210")

