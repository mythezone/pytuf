"""
Created on : 2024-07-13
Created by : Mythezone
Updated by : Mythezone
Email      : mythezone@gmail.com
FileName   : ~/project/simlob-refined/log/logger.py
Description: Loggers for this project
---
Updated    : 
---
Todo       : 
"""
# Insert the path into sys.path for importing.
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


import logging
from .config import ConfigManager as CM
import datetime, shutil

cm = CM()

# 配置日志记录器
def setup_logger(log_type:str="", logger_name:str="default",logging_level:int=logging.DEBUG):
    # 创建一个日志记录器
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_level)  # 设置日志记录器的级别为DEBUG
    
    # 创建一个文件处理器，用于将日志写入文件
    if log_type=='clean':
        # 'generator'
        log_file = cm.logs.clean
    elif log_type=='download':
        # 'result'
        log_file = cm.logs.download
    else:
        # 'default'
        log_file = cm.logs.default
    
    
    # 如果记录文件过大,就移到archived日志中,重新记录
    if os.path.exists(log_file) and os.path.getsize(log_file) > 10*1024*1024:
        archive_dir = cm.logs.archived
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir,exist_ok=True)
        archive_file = os.path.join(archive_dir,f"{os.path.basename(log_file)}_{datetime.now().strftime("%Y%m%d%H%M%S")}.log") 
        shutil.move(log_file,archive_file)
        print(f"Archived Log file to {archive_file}")
        
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging_level)
    
    # 创建一个日志格式器，并将其添加到文件处理器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # 将文件处理器添加到日志记录器
    logger.addHandler(file_handler)
    
    return logger

# # 使用日志记录器
# logger = setup_logger('default')

# # 记录各种级别的日志
# logger.debug('This is a debug message')
# logger.info('This is an info message')
# logger.warning('This is a warning message')
# logger.error('This is an error message')
# logger.critical('This is a critical message')

# print("Logs have been written to my_log.log")