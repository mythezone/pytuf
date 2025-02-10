import os
import logging

logger = logging.getLogger(__name__)

def get_info_path_by_code(code, info_path=r"\\10.16.12.105\disk\G\Info"):
    """
    根据代码生成信息存储路径
    Args:
        code (str): 文件编码
        info_path (str): 基础路径
    Returns:
        str: 生成的完整路径
    """
    first_letter = code[0]
    first_3_letters = code[:3]
    folder = os.path.join(info_path, first_letter, first_3_letters, code)
    os.makedirs(folder, exist_ok=True)  # 创建目录，如果存在则不创建
    return folder

def multi_pipeline(root_path):
    """多线程处理pipeline（需实现具体的multi_pipeline逻辑）"""
    pass  # 根据需求实现具体逻辑

def multi_thread_pipeline():
    """
    多线程处理所有Adult文件夹
    Returns:
        None
    """
    paths = [
        r"\\10.16.12.105\disk\media\16t\Adult",
        r"\\10.16.12.105\disk\G\Adult",
        r"\\10.16.12.105\disk\D\Adult",
        r"\\10.16.12.105\disk\J\Adult",
        r"\\10.16.12.105\disk\media\4t\Adult",
        r"\\10.16.12.105\disk\media\4t2\Adult"
    ]
    
    for path in paths:
        try:
            multi_pipeline(path)
            logger.info(f"Processed path: {path}")
        except Exception as e:
            logger.error(f"Error processing {path}: {str(e)}")