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

from tools.movie_javdb import get_movie_json_by_url
from tools.process_json import process_json
# from frontend.movie.parser import parse_json
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
from tools.movie_javdb import multi_thread_pipeline
import subprocess



class TorrentDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Torrent Downloader")
        self.geometry("400x400")

        self.cm = ConfigManager()
        
        self.qb_downloader = None
        self.monitoring = False
        self.scanning = False 
        
        self.current_label = datetime.now().strftime("%Y-%m-%d")
        self.create_widgets()
        
    def create_widgets(self):
        self.date_label = tk.Label(self, text=f"Current Date: {self.current_label}", wraplength=380)
        self.date_label.pack(pady=10)
        
        self.label = tk.Label(self, text="Clipboard content will appear here", wraplength=380)
        self.label.pack(pady=10)

        self.start_button = tk.Button(self, text="开始监控", command=self.start_monitoring)
        self.start_button.pack(pady=10)

        self.view_downloads_button = tk.Button(self, text="View Downloads", command=self.view_downloads)
        self.view_downloads_button.pack(pady=10)
        
        self.movie_button = tk.Button(self, text="Start Server", command=self.start_server)
        self.movie_button.pack(pady=10)
        
        self.scan_button = tk.Button(self, text="Scan Folders", command=self.start_scan_folder)
        self.scan_button.pack(pady=10)

    def start_server(self):
        def start():
            os.system(r"C:\Users\mythezone\.conda\envs\web\python.exe manage.py runserver 192.168.50.116:19880")
        
        self.start_server_threading = threading.Thread(target=start)
        self.start_server_threading.start()

    def start_monitoring(self):
        """开始监控剪贴板"""
        if self.qb_downloader is None:
            if not self.read_config_and_login():
                return  # 连接失败，不启动监控
        
        # if self.qb_downloader and self.qb_downloader.session:
        if not self.monitoring:
            self.monitoring = True
            self.monitor_threading = threading.Thread(target=self.monitor_clipboard)
            self.monitor_threading.daemon = True  # 设置为守护线程
            self.monitor_threading.start()
            self.start_button.config(text="停止监控", command=self.stop_monitoring)
            print("监控已启动", "剪贴板监控已启动！")
        else:
           print("提示", "监控已在运行中")
        # else:
        #     messagebox.showerror("错误", "无法连接到 qBittorrent，监控未启动")
            
    def stop_monitoring(self):
        """停止监控剪贴板"""
        if self.monitoring:
            self.monitoring = False
            if hasattr(self, 'monitor_threading') and self.monitor_threading.is_alive():
                self.monitor_threading.join(timeout=1)  # 等待线程结束，最多1秒
            self.start_button.config(text="开始监控", command=self.start_monitoring)
            messagebox.showinfo("监控已停止", "剪贴板监控已停止！")
        else:
            messagebox.showinfo("提示", "监控未在运行")
            
    def start_scan_folder(self):
        if self.scanning == False:
            self.scanning = True 
            self.scan_threading = threading.Thread(target=multi_thread_pipeline)
            self.scan_threading.start()
            
        else:
            self.scanning = False 
            self.scan_threading.join()
        

    def read_config_and_login(self):
        """读取配置并登录到 qBittorrent"""
        try:
            qb_url = self.cm.servers.url
            username = self.cm.servers.username
            password = self.cm.servers.password

            print(f"正在连接到 qBittorrent: {qb_url}")
            print(f"用户名: {username}")
            print(f"密码长度: {len(password)}")
            self.qb_downloader = QBTorrentDownloader(qb_url, username, password)
            
            if not self.qb_downloader.session:
                error_msg = ("无法连接到 qBittorrent！\n\n"
                           "请检查以下项目：\n"
                           "1. qBittorrent 是否正在运行\n"
                           "2. Web UI 是否已启用\n"
                           "   (工具 -> 选项 -> Web UI -> 启用 Web 用户界面)\n"
                           "3. URL 和端口是否正确\n"
                           f"   当前配置: {qb_url}\n"
                           "4. 用户名和密码是否正确\n\n"
                           "如果 qBittorrent 正在运行但仍然连接失败，\n"
                           "请尝试重启 qBittorrent 应用程序。")
                messagebox.showerror("连接失败", error_msg)
                return False
            else:
                # 测试连接
                if self.qb_downloader.is_connected():
                    messagebox.showinfo("连接成功", "已成功连接到 qBittorrent!")
                    return True
                else:
                    messagebox.showerror("连接测试失败", "登录成功但连接测试失败，请检查 qBittorrent 状态。")
                    return False
                    
        except Exception as e:
            error_msg = f"读取配置或连接时发生错误：\n{str(e)}"
            messagebox.showerror("配置错误", error_msg)
            return False
            
    def get_movie_info_by(self,url):
        info = get_movie_json_by_url(url = url)
        process_json(j = info)
        # parse_json(j=info)

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
                elif clipboard_content.endswith('.mp4') or clipboard_content.endswith('.mkv'):
                    self.label.config(text=clipboard_content)
                    subprocess.run([r"C:\mythezone\tools\PotPlayer\PotPlayerMini64.exe", clipboard_content])
                    
            time.sleep(2)
            
    def view_downloads(self):
        """查看下载列表"""
        if self.qb_downloader is None:
            if not self.read_config_and_login():
                return
                
        if not self.qb_downloader or not self.qb_downloader.session:
            messagebox.showerror("错误", "必须先连接到 qBittorrent")
            return

        try:
            torrents = self.qb_downloader.get_torrents_by_label(self.current_label)
            if not torrents:
                messagebox.showinfo("无下载", f"标签 '{self.current_label}' 下没有下载任务")
                return

            view_window = tk.Toplevel(self)
            view_window.title("当前下载")
            view_window.geometry("800x400")

            columns = ("Name", "Size", "Progress", "State")
            tree = ttk.Treeview(view_window, columns=columns, show="headings")
            tree.heading("Name", text="名称")
            tree.heading("Size", text="大小")
            tree.heading("Progress", text="进度")
            tree.heading("State", text="状态")

            # 设置列宽
            tree.column("Name", width=400)
            tree.column("Size", width=100)
            tree.column("Progress", width=100)
            tree.column("State", width=100)

            for torrent in torrents:
                size_mb = torrent.get('total_size', 0) / (1024 * 1024)
                progress = torrent.get('progress', 0) * 100
                tree.insert("", "end", values=(
                    torrent.get('name', 'N/A'),
                    f"{size_mb:.2f} MB",
                    f"{progress:.2f}%",
                    torrent.get('state', 'N/A')
                ))

            tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取下载列表时发生错误：\n{str(e)}")
        
    def on_closing(self):
        """关闭应用程序时的清理工作"""
        try:
            # 停止监控
            if self.monitoring:
                self.monitoring = False
                if hasattr(self, 'monitor_threading') and self.monitor_threading.is_alive():
                    self.monitor_threading.join(timeout=2)
            
            # 停止扫描
            if self.scanning:
                self.scanning = False
                if hasattr(self, 'scan_threading') and self.scan_threading.is_alive():
                    self.scan_threading.join(timeout=2)
            
            # 停止服务器
            if hasattr(self, 'start_server_threading') and self.start_server_threading.is_alive():
                # 注意：服务器线程可能需要手动停止
                pass
                
        except Exception as e:
            print(f"关闭应用程序时发生错误: {e}")
        finally:
            self.destroy()


if __name__ == "__main__":
    app = TorrentDownloaderApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)  # 绑定关闭事件
    app.mainloop()