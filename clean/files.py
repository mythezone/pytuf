"""
Created on : 2024-07-13
Created by : Mythezone
Updated by : Mythezone
Email      : mythezone@gmail.com
FileName   : ~/project/simlob-refined/config/config.py
Description: Configuration Class
---
Updated    : 
---
Todo       : 
"""

# Insert the path into sys.path for importing.
import sys,os,json
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logger import setup_logger

logger = setup_logger()
    
def delete_small_files(folder_path, min_size_mb=100):
    min_size_bytes = min_size_mb * 1024 * 1024  # 将MB转换为字节
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            if file_size < min_size_bytes:
                os.remove(file_path)
                logger.info(f"Deleted: {file_path}, Size: {file_size / (1024 * 1024):.2f} MB")