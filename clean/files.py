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
import re, shutil

logger = setup_logger()
    
def delete_small_files(folder_path, min_size_mb=200):
    min_size_bytes = min_size_mb * 1024 * 1024  # 将MB转换为字节
    
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            if file_size < min_size_bytes:
                os.remove(file_path)
                logger.info(f"Deleted: {file_path}, Size: {file_size / (1024 * 1024):.2f} MB")


def delete_empty_folders(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # 如果文件夹是空的
                os.rmdir(dir_path)
                logger.info(f"Deleted empty folder: {dir_path}")
                
                

def move_large_videos(source_folder, target_folder, min_size_gb=1):
    min_size_bytes = min_size_gb * 1024 * 1024 * 1024  # 将GB转换为字节
    pattern = re.compile(r'\b[a-zA-Z]{3,4}-\d{3,4}\b')

    for root, dirs, files in os.walk(source_folder):
        for file in files:
            file_path = os.path.join(root, file)
            file_size = os.path.getsize(file_path)
            file_extension = os.path.splitext(file)[1]

            if file_extension == '.!qB':
                logger.info(f"Skipping incomplete file: {file_path}")
                continue
            
            if file_size > min_size_bytes:
                match = pattern.search(file)
                
                if match:
                    new_file_name = match.group() + file_extension
                else:
                    print(f"Filename pattern not found for: {file}")
                    new_file_name = input("Please enter the new filename (without extension): ") + file_extension
                
                first_letter = new_file_name[0].upper()
                sub_folder = new_file_name[:3].upper()
                target_sub_folder = os.path.join(target_folder, first_letter, sub_folder, new_file_name[:-len(file_extension)])
                
                os.makedirs(target_sub_folder, exist_ok=True)
                
                new_file_path = os.path.join(target_sub_folder, new_file_name)
                
                shutil.move(file_path, new_file_path)
                logger.info(f"Moved: {file_path} to {new_file_path}")
                    
def clean_download_folder(source_folder,target_folder):
    delete_small_files(source_folder)
    
    delete_empty_folders(source_folder)
    
    move_large_videos(source_folder,target_folder)
    
    delete_empty_folders(source_folder)
    

if __name__ == "__main__":
    clean_download_folder(r"\\10.16.51.226\media\16t\downloads",r"\\10.16.51.226\media\16t\Adult_tmp")
    source_folder = r"\\10.16.51.226\media\16t\downloads"
    # delete_small_files(source_folder)
    
    # delete_empty_folders(source_folder)