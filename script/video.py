import subprocess
import json
import os

def get_video_info(video_path):
    """
    获取视频基本信息，包括编码、时长、帧率、分辨率以及文件大小。
    
    参数:
        video_path: 视频文件的路径
    
    返回:
        包含视频信息的字典，示例:
        {
            'codec': 'h264',
            'duration': 120.5,  # 单位：秒
            'fps': 29.97,
            'width': 1920,
            'height': 1080,
            'file_size': 12345678  # 单位：字节
        }
    """
    # 使用 ffprobe 命令获取视频的 JSON 格式元数据
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,r_frame_rate',
        '-show_entries', 'format=duration,size',
        '-of', 'json',
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=True)
        data = json.loads(result.stdout)
    except Exception as e:
        print(f"调用 ffprobe 失败: {e}")
        return {}
    
    # 获取视频流信息
    streams = data.get('streams', [])
    if not streams:
        print("没有检测到视频流信息。")
        return {}
    video_stream = streams[0]
    
    # 提取格式信息（时长、文件大小）
    format_info = data.get('format', {})
    
    # 解析时长和文件大小
    duration = float(format_info.get('duration', 0))
    file_size = int(format_info.get('size', 0))
    
    # 获取编码、宽度、高度
    codec = video_stream.get('codec_name', 'Unknown')
    width = video_stream.get('width', 0)
    height = video_stream.get('height', 0)
    
    # 解析帧率，r_frame_rate 通常为 "30000/1001" 格式
    r_frame_rate = video_stream.get('r_frame_rate', '0/0')
    try:
        num, denom = r_frame_rate.split('/')
        fps = float(num) / float(denom) if float(denom) != 0 else 0.0
    except Exception:
        fps = 0.0
    
    return {
        'codec': codec,
        'duration': duration / 60,  # 转换为分钟
        'fps': fps,
        'width': width,
        'height': height,
        'file_size': file_size / 1024 / 1024 / 1024,    # 转换为 GB,
    }

# 示例调用
if __name__ == "__main__":
    video_path = r"\\10.16.51.242\media\4t2\Adult\A\AARM-207\AARM-207.mp4"  # 替换为你的视频文件路径
    info = get_video_info(video_path)
    print(info)
