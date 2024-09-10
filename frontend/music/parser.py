from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from pprint import pprint

# 加载 MP3 文件
audio = MP3(r"sample\02.mp3")

# 提取元数据
title = audio.get('title', ['Unknown'])[0]
artist = audio.get('artist', ['Unknown'])[0]
album = audio.get('album', ['Unknown'])[0]
duration = audio.info.length
# output_image_path = r"extract\02.jpg"
# for tag in audio.tags.values():
    
#     if isinstance(tag, APIC):
#         # 提取封面图数据
#         with open(output_image_path, 'wb') as img_file:
#             img_file.write(tag.data)
#         print(f"封面图已保存到 {output_image_path}")
#     else:
#         print(f"未找到封面图, in {tag}")

pprint(audio.__dict__)



