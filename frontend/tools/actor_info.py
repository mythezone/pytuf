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

from tools.process_json import process_json

from tools.base import get_response_by_url, sessions, new_session, headers, save_resource_by_url  