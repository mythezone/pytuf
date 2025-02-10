import os
import logging

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
                        logger.info(f"Deleted empty folder: {dir_path}")
                    except OSError as e:
                        logger.warning(f"Failed to delete folder: {dir_path}, reason: {str(e)}")
    except Exception as e:
        logger.error(f"Error in deleting empty folders: {str(e)}")