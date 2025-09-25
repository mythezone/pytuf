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
from utils.config import ConfigManager
import time
import pyperclip
import requests
from datetime import datetime
from requests.exceptions import ConnectionError, Timeout, RequestException

class QBTorrentDownloader:
    def __init__(self, qb_url, username, password):
        self.qb_url = qb_url
        self.username = username
        self.password = password
        self.logger = setup_logger("download")
        self.session = self.login()
        
    def _get_headers(self):
        """获取标准的请求头"""
        return {
            'Referer': self.qb_url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def login(self, max_retries=3, timeout=10):
        """
        登录到 qBittorrent Web UI
        
        Args:
            max_retries: 最大重试次数
            timeout: 连接超时时间（秒）
        
        Returns:
            requests.Session 对象或 None
        """
        for attempt in range(max_retries):
            try:
                session = requests.Session()
                # 设置连接和读取超时
                session.timeout = timeout
                
                # 首先访问主页获取可能的CSRF token或session cookies
                try:
                    self.logger.info(f"访问主页获取session: {self.qb_url}")
                    home_response = session.get(self.qb_url, headers=self._get_headers(), timeout=timeout)
                    print(f"主页访问状态码: {home_response.status_code}")
                except Exception as e:
                    print(f"主页访问失败: {e}")
                
                login_data = {'username': self.username, 'password': self.password}
                
                self.logger.info(f"尝试连接到 qBittorrent: {self.qb_url} (第 {attempt + 1} 次)")
                
                response = session.post(
                    f'{self.qb_url}/api/v2/auth/login', 
                    data=login_data,
                    headers=self._get_headers(),
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    # 检查响应内容来确认登录是否真正成功
                    response_text = response.text.strip()
                    print(f"DEBUG: 响应内容: '{response_text}' (长度: {len(response_text)})")
                    print(f"DEBUG: 响应内容 (repr): {repr(response_text)}")

                    # qBittorrent API 响应逻辑：
                    # - HTTP 200 + "fails" = 明确失败
                    # - HTTP 200 + 其他内容 = 成功（包括 "ok", 空响应等）
                    if response_text.lower() == 'fails':
                        self.logger.error("登录失败: 用户名或密码错误")
                        print(f"登录失败: HTTP状态码 {response.status_code}")
                        print("登录失败: 用户名或密码错误")
                    else:
                        # HTTP 200 且不是明确失败，则认为成功
                        self.logger.info(f"qBittorrent 登录成功! (响应: '{response_text}')")
                        print(f"qBittorrent 登录成功! (响应: '{response_text}')")
                        return session
                else:
                    self.logger.error(f"登录失败: HTTP状态码 {response.status_code}")
                    print(f"登录失败: HTTP状态码 {response.status_code}")
                    
            except ConnectionError as e:
                error_msg = f"连接错误 (第 {attempt + 1} 次尝试): {e}"
                self.logger.error(error_msg)
                print(error_msg)
                if "Remote end closed connection without response" in str(e):
                    hint_msg = "提示: qBittorrent 可能未启动或 Web UI 未启用"
                    self.logger.warning(hint_msg)
                    print(hint_msg)
                
            except Timeout as e:
                error_msg = f"连接超时 (第 {attempt + 1} 次尝试): {e}"
                self.logger.error(error_msg)
                print(error_msg)
                hint_msg = "提示: 检查网络连接或增加超时时间"
                self.logger.warning(hint_msg)
                print(hint_msg)
                
            except RequestException as e:
                error_msg = f"请求错误 (第 {attempt + 1} 次尝试): {e}"
                self.logger.error(error_msg)
                print(error_msg)
                
            except Exception as e:
                error_msg = f"未知错误 (第 {attempt + 1} 次尝试): {e}"
                self.logger.error(error_msg)
                print(error_msg)
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                wait_msg = f"等待 {wait_time} 秒后重试..."
                self.logger.info(wait_msg)
                print(wait_msg)
                time.sleep(wait_time)
        
        final_error_msg = "所有连接尝试都失败了!"
        self.logger.error(final_error_msg)
        print(final_error_msg)
        
        hints = [
            "请检查:",
            "1. qBittorrent 是否正在运行",
            "2. Web UI 是否已启用 (工具 -> 选项 -> Web UI)",
            "3. URL 和端口是否正确",
            "4. 用户名和密码是否正确"
        ]
        for hint in hints:
            self.logger.warning(hint)
            print(hint)
        
        return None

    def download(self, torrent_url, label, timeout=30):
        """
        下载种子
        
        Args:
            torrent_url: 磁力链接或种子文件URL
            label: 标签
            timeout: 请求超时时间
        """
        if not self.session:
            self.logger.error("Session is not authenticated")
            return False
            
        try:
            payload = {
                'urls': torrent_url,
                'tags': label
            }
            
            self.logger.info(f"正在添加下载: {torrent_url}")
            response = self.session.post(
                f'{self.qb_url}/api/v2/torrents/add', 
                data=payload,
                headers=self._get_headers(),
                timeout=timeout
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully added torrent: {torrent_url}")
                return True
            else:
                self.logger.warning(f"Failed to add torrent: {torrent_url}, HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"下载时发生错误: {e}")
            return False
            
    def get_all_torrents(self, timeout=10):
        """
        获取所有种子信息
        
        Args:
            timeout: 请求超时时间
        
        Returns:
            种子列表或空列表
        """
        if not self.session:
            self.logger.error("Session is not authenticated")
            return []
            
        try:
            response = self.session.get(
                f'{self.qb_url}/api/v2/torrents/info',
                headers=self._get_headers(),
                timeout=timeout
            )
            
            if response.status_code == 200:
                self.logger.info("All torrent information got.")
                return response.json()
            else:
                self.logger.warning(f"Failed to get torrent information, HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取种子信息时发生错误: {e}")
            return []
        
    def get_torrents_by_label(self, label, timeout=10):
        """
        根据标签获取种子列表
        
        Args:
            label: 标签名
            timeout: 请求超时时间
        
        Returns:
            种子列表或空列表
        """
        if not self.session:
            self.logger.error("Session is not authenticated")
            return []
            
        try:
            response = self.session.get(
                f'{self.qb_url}/api/v2/torrents/info',
                params={'tag': label},
                headers=self._get_headers(),
                timeout=timeout
            )
            
            if response.status_code == 200:
                torrents = response.json()
                filtered_torrents = [torrent for torrent in torrents if label in torrent.get('tags', '')]
                self.logger.info(f"Found {len(filtered_torrents)} torrents with label '{label}'")
                return filtered_torrents
            else:
                self.logger.warning(f"Failed to get torrent information, HTTP {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取标签种子列表时发生错误: {e}")
            return []

    def is_connected(self):
        """
        检查是否连接到 qBittorrent
        
        Returns:
            bool: True 如果连接正常，否则 False
        """
        if not self.session:
            return False
            
        try:
            response = self.session.get(f'{self.qb_url}/api/v2/app/version', headers=self._get_headers(), timeout=5)
            return response.status_code == 200
        except:
            return False