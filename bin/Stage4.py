import os
from PIL import Image
import subprocess

try:
    # 获取当前文件夹路径
    folder_path = os.path.dirname(os.getcwd())
    frame_path = os.path.join(folder_path, "video_frame_Done")  #定义图像成品文件夹

    # 定义文件路径
    video_filename = os.path.join(folder_path, "video.mp4")
    music_filename = os.path.join(folder_path, "video.mp3")
    video_out_filename = os.path.join(folder_path, "video_Done.mp4")

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
        #frame_files = [os.path.join(image_folder, file) for file in os.listdir(image_folder) if file.endswith('.png')]

        # 调用FFmpeg将图片合成为视频
        subprocess.run(['ffmpeg', '-i', frame_path, '-r', str(fps), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '0', '-y', output_video])
        
        # 调用FFmpeg将音乐合成进视频
        subprocess.call(['ffmpeg', '-i', output_video, '-i', music_file, '-c:v', 'copy', '-c:a', 'mp3', '-map', '0:v:0', '-map', '1:a:0', '-shortest', '-y', output_video])

    # 输出原视频音频文件
    extract_music_from_video(video_filename,music_filename)

    # 输出最终视频文件
    fps = input("请输入想要输出的视频帧率（默认15）：") or 15   # 定义fps，默认15帧/秒
    convert_images_to_video(frame_path,video_out_filename,music_filename)

except Exception as e:
    print(f"error file: {e.__traceback__.tb_frame.f_globals[__file__]}\n")
    print(f"error line: {e.__traceback__.tb_lineno}\n")
    print(e)
