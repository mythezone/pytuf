
from pprint import pprint
# Insert the path into sys.path for importing.
import sys
import os
import json 
import shutil

sys.path.append(r"C:\Users\mythezone\Documents\project\python\pytuf\frontend")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'frontend.settings')
import django  
django.setup()

from movie.models import Movie, Magnet
from person.models import Group
from movie.parser import parse_json

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        else:
            if event.src_path.endswith(".json"):
                parse_json(event.src_path)
                print(f"New file created: {event.src_path}")
        
def monitor_directory(path):
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(20)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    
if __name__ == "__main__":
    monitor_directory(r"\\10.16.12.105\disk\G\Info")