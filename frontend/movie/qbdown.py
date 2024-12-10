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

class QBTorrentDownloader:
    def __init__(self, qb_url, username, password):
        self.qb_url = qb_url
        self.username = username
        self.password = password
        self.session = self.login()
        self.logger = setup_logger("download")
        self.cm = ConfigManager()

    def login(self):
        session = requests.Session()
        login_data = {'username': self.username, 'password': self.password}
        response = session.post(f'{self.qb_url}/api/v2/auth/login', data=login_data)
        if response.status_code == 200:
            print("Login successful")
        else:
            print("Login failed")
            session = None
        return session

    def download(self, torrent_url,label):
        if self.session:
            payload = {'urls': torrent_url,
                       'tags': label
                       }
            response = self.session.post(f'{self.qb_url}/api/v2/torrents/add', data=payload)
            if response.status_code == 200:
                self.logger.info(f"Successfully added torrent: {torrent_url}")
            else:
                self.logger.warning(f"Failed to add torrent: {torrent_url}")
        else:
            self.logger.error("Session is not authenticated")
            
    def get_all_torrents(self):
        if self.session:
            response = self.session.get(f'{self.qb_url}/api/v2/torrents/info')
            if response.status_code == 200:
                self.logger.info("All torrent inforamtion got.")
                return response.json()
            else:
                self.logger.warning("Failed to get torrent information")
                return []
        else:
            self.logger.error("Session is not authenticated")
            return []
        
    def get_torrents_by_label(self, label):
        if self.session:
            response = self.session.get(f'{self.qb_url}/api/v2/torrents/info')
            if response.status_code == 200:
                torrents = response.json()
                return [torrent for torrent in torrents if label in torrent.get('tags', '')]
            else:
                self.logger.warning("Failed to get torrent information")
                return []
        else:
            self.logger.error("Session is not authenticated")
            return []