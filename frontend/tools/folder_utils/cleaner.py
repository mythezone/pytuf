import os
import logging
from rich import print 

logger = logging.getLogger(__name__)

def delete_empty_folders(folder_path):
    """
    删除指定路径下的所有空文件夹
    Args:
        folder_path (str): 需要清理的根目录路径
    Returns:
        None
    """
    try:
        for root, dirs, files in os.walk(folder_path, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                if not os.listdir(dir_path):  # 检查文件夹是否为空
                    try:
                        os.rmdir(dir_path)
                        print(f"Deleted empty folder: {dir_path}")
                    except OSError as e:
                        logger.warning(f"Failed to delete folder: {dir_path}, reason: {str(e)}")
    except Exception as e:
        logger.error(f"Error in deleting empty folders: {str(e)}")
        
        
def delete_small_files(folder_path, size_limit=1024):
    """
    删除指定路径下小于指定大小的文件
    Args:
        folder_path (str): 需要清理的根目录路径
        size_limit (int): 文件大小下限，单位：KB，默认为 1024 KB
    Returns:
        None
    """
    
    try:
        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.!qB'):
                    continue
                file_path = os.path.join(root, file_name)
                file_size = os.path.getsize(file_path) / 1024    # 文件大小，单位：KB
                if file_size < size_limit:
                    try:
                        os.remove(file_path)
                        print(f"Deleted small file: {file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to delete file: {file_path}, reason: {str(e)}")
    except Exception as e:
        logger.error(f"Error in deleting small files: {str(e)}")
        
if __name__ == "__main__":
    delete_small_files(r"\\10.16.51.242\media\4t\downloads")
    delete_empty_folders(r"\\10.16.51.242\media\4t\downloads")
    