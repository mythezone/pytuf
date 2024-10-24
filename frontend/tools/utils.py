from pathlib import Path
import shutil
import os


def del_movie_by_filename(filename):
    parent_folder = Path(filename).parent
    shutil.rmtree(parent_folder)