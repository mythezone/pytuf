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

from frontend.tools.movie_javdb import get_movie_json_by_url
from frontend.tools.process_json import process_json

from utils.logger import setup_logger
from utils.config import ConfigManager
from movie.qbdown import QBTorrentDownloader
import tkinter as tk
from tkinter import messagebox, ttk 
import pyperclip
import requests
import time
import threading
import configparser
from datetime import datetime



class TorrentDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Torrent Downloader")
        self.geometry("400x200")

        self.cm = ConfigManager()
        
        self.qb_downloader = None
        self.monitoring = False
        
        self.current_label = datetime.now().strftime("%Y-%m-%d")
        self.create_widgets()
        
    def create_widgets(self):
        self.date_label = tk.Label(self, text=f"Current Date: {self.current_label}", wraplength=380)
        self.date_label.pack(pady=10)
        
        self.label = tk.Label(self, text="Clipboard content will appear here", wraplength=380)
        self.label.pack(pady=10)

        self.start_button = tk.Button(self, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(pady=10)

        self.view_downloads_button = tk.Button(self, text="View Downloads", command=self.view_downloads)
        self.view_downloads_button.pack(pady=10)

    def start_monitoring(self):
        if self.qb_downloader is None:
            self.read_config_and_login()
        
        if self.qb_downloader.session:
            self.monitoring = True
            threading.Thread(target=self.monitor_clipboard).start()

    def read_config_and_login(self):

        qb_url = self.cm.servers.url
        username = self.cm.servers.username
        password = self.cm.servers.password

        self.qb_downloader = QBTorrentDownloader(qb_url, username, password)
        if not self.qb_downloader.session:
            messagebox.showerror("Login Failed", "Could not log in to qBittorrent. Check your credentials.")
            
    def get_movie_info_by(self,url):
        info = get_movie_json_by_url(url = url)
        process_json(j = info)

    def monitor_clipboard(self):
        recent_value = ""
        while self.monitoring:
            clipboard_content = pyperclip.paste()
            if clipboard_content != recent_value:
                recent_value = clipboard_content
                if 'magnet:?' in clipboard_content or clipboard_content.endswith('.torrent'):
                    self.label.config(text=clipboard_content)
                    self.qb_downloader.download(clipboard_content,self.current_label)
                elif "https://javdb.com/v/" in clipboard_content:
                    self.label.config(text=clipboard_content)
                    threading.Thread(target=self.get_movie_info_by, args=(clipboard_content,)).start()
                    # info = get_movie_json_by_url(url = clipboard_content)
                    
                    # process_json(j = info)
            time.sleep(2)
            
    def view_downloads(self):
        if self.qb_downloader is None:
            messagebox.showerror("Error", "You must start monitoring first.")
            return

        torrents = self.qb_downloader.get_torrents_by_label(self.current_label)
        if not torrents:
            messagebox.showinfo("No Downloads", "No downloads to display.")
            return

        view_window = tk.Toplevel(self)
        view_window.title("Current Downloads")
        view_window.geometry("600x400")

        columns = ("Name", "Size", "Progress", "State")
        tree = ttk.Treeview(view_window, columns=columns, show="headings")
        tree.heading("Name", text="Name")
        tree.heading("Size", text="Size")
        tree.heading("Progress", text="Progress")
        tree.heading("State", text="State")

        for torrent in torrents:
            tree.insert("", "end", values=(
                torrent['name'],
                f"{torrent['total_size'] / (1024 * 1024):.2f} MB",
                f"{torrent['progress'] * 100:.2f} %",
                torrent['state']
            ))

        tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
    def on_closing(self):
        if self.monitoring:
            self.monitoring = False
            self.monitor_thread.join()
        self.destroy()


if __name__ == "__main__":
    app = TorrentDownloaderApp()
    app.mainloop()