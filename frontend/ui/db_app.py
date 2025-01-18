import sys
import random
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from pymongo import MongoClient
from pprint import pprint
import json
from bson import ObjectId

from db_user import User 


class MovieDialog(QDialog):
    def __init__(self, movies, parent=None):
        super(MovieDialog, self).__init__(parent)
        self.movies_ids = movies
        self.current_movie_index = 0
        self.current_screenshot_index = 0
        self.client = MongoClient("mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin")
        self.db = self.client['myj']
        self.movie_collection = self.db['movie']
        self.user = User("mythezone","")
        # pprint(self.movies)
        
        self.movies_cur = self.movie_collection.find({"_id": {"$in": [ObjectId(movie['id']) for movie in self.movies_ids]}})
        
        self.movies = []
        # 获取self.movies的总数
        for doc in self.movies_cur:
            self.movies.append(doc)
            
        self.total = len(self.movies)
        
           
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Movies')
        self.setGeometry(200, 200, 1920, 1080)

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.movie_title_label = QLabel(self)
        self.movie_image_label = QLabel(self)
        
        # self.movie_image_label.setScaledContents(True)
        # self.movie_image_label.setAutoFillBackground(True)
        self.movie_image_label.setFixedSize(1920,1080)
        self.movie_image_label.setAlignment(Qt.AlignCenter)
        

        
        self.main_layout.addWidget(self.movie_title_label)
        self.main_layout.addWidget(self.movie_image_label)

        self.button_layout = QHBoxLayout()
        self.prev_button = QPushButton('Previous', self)
        self.prev_button.clicked.connect(self.show_previous_movie)
        self.next_button = QPushButton('Next', self)
        self.next_button.clicked.connect(self.show_next_movie)
        self.add_movie_button = QPushButton('Add to Favorite', self)
        self.add_movie_button.clicked.connect(lambda: self.user.add_movie(self.movies[self.current_movie_index]['_id'], "fav_movie"))
        self.del_movie_button = QPushButton('Del from Favorite', self)
        self.del_movie_button.clicked.connect(lambda: self.user.del_movie(self.movies[self.current_movie_index]['_id'], "fav_movie"))
        self.add_movie_hate_button = QPushButton('Add to Hate', self)
        self.add_movie_hate_button.clicked.connect(lambda: self.user.add_movie(self.movies[self.current_movie_index]['_id'], "hate_movie"))
        
        self.button_layout.addWidget(self.add_movie_button)
        self.button_layout.addWidget(self.del_movie_button)
        
        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.next_button)
        self.main_layout.addLayout(self.button_layout)

        self.setLayout(self.main_layout)
        self.show_movie()

    def show_movie(self):
        # movie_id = self.movies[self.current_movie_index]['id']
        # print(movie_id)
        # movie_doc = self.movie_collection.find_one({"_id": ObjectId(movie_id)})
        movie_doc = self.movies[self.current_movie_index]

        if movie_doc:
            self.movie_title_label.setText(movie_doc['title'])
            self.show_screenshot(movie_doc)

    def show_screenshot(self, movie_doc):
        screenshots = movie_doc.get('screenshots', [])
        # print(screenshots)
        if screenshots:
            screenshot_path = self.get_image_file_by_url(screenshots[self.current_screenshot_index])
            pixmap = QPixmap()
            with open(screenshot_path, 'rb') as f:
                pixmap.loadFromData(f.read())
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.movie_image_label.width(),self.movie_image_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.movie_image_label.setPixmap(scaled_pixmap)
                self.movie_image_label.adjustSize()
            else:
                    print("Failed to load pixmap from file")
        else:
            print(f"File does not exist: {screenshot_path}") 


    def get_image_file_by_url(self, img_url):
        hash_name, img_name = img_url.split(':')
        img_path = os.path.join(r"\\10.16.12.105\disk\D\Pictures\J_IMG_LIB\movie", hash_name[:2],hash_name[2:4], img_name)
        print(img_path)
        return img_path

    def show_previous_movie(self):
        if len(self.movies) == 0:
            return
        
        self.current_movie_index = (self.current_movie_index - 1) % self.total
        self.current_screenshot_index = 0
        self.show_movie()

    def show_next_movie(self):
        self.current_movie_index = (self.current_movie_index + 1) % self.total
        self.current_screenshot_index = 0
        self.show_movie()

    def mousePressEvent(self, event):
        l = len(self.movies[self.current_movie_index].get('screenshots', []))
        pprint(self.movies[self.current_movie_index])
        if l == 0:
            return 
        
        if  event.button() == Qt.LeftButton:
            self.current_screenshot_index = (self.current_screenshot_index + 1) % l
            self.show_movie()

class ActressDetailApp(QWidget):
    def __init__(self):
        super().__init__()
        self.client = MongoClient("mongodb://mythezone:19891016Zmy!@10.16.12.105:27017/admin")
        self.db = self.client['myj']
        self.collection = self.db['actress']
        self.user = User("mythezone","")
        self.initUI()
        

    def initUI(self):
        self.setWindowTitle('Actress Detail')
        self.setGeometry(100, 100, 1080,720)

        # Create main layout
        self.main_layout = QHBoxLayout()

        # Left side: Avatar
        # self.avatar_label = QLabel(self)
        # self.avatar_label.setScaledContents(True)
        # self.avatar_label.setFixedSize(300, 300)
        self.avatar_label = QLabel(self)
        self.avatar_label.setScaledContents(True)
        self.avatar_label.setFixedWidth(540)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        
        self.avatar_label.mousePressEvent = self.show_movies_dialog
        self.main_layout.addWidget(self.avatar_label)

        # Right side: Details
        self.details_layout = QVBoxLayout()

        # Add scroll area for details
        self.scroll_area = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.details_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        # Add button to refresh actress details
        self.refresh_button = QPushButton('Refresh', self)
        self.refresh_button.clicked.connect(self.refresh_actress)
        self.details_layout.addWidget(self.refresh_button)

        self.setLayout(self.main_layout)

        # Load initial actress
        self.refresh_actress()

    def refresh_actress(self):
        actress_doc = self.get_random_not_hated_actress_doc()
        if actress_doc:
            self.update_ui(actress_doc)
            
    def get_random_not_hated_actress_doc(self):
        count = self.collection.count_documents({"avatar_parsed": True, "movies": {"$exists": True}})
        random_index = random.randint(0, count - 1)
        actress_doc = self.collection.find({"avatar_parsed": True}).skip(random_index).limit(1).next()
        actress_id = str(actress_doc['_id'])
        hate_actress = self.user.user.get("hate_actress",[])
        while actress_id in hate_actress:
            random_index = random.randint(0, count - 1)
            actress_doc = self.collection.find({"avatar_parsed": True}).skip(random_index).limit(1).next()
            actress_id = str(actress_doc['_id'])
        return actress_doc

    def get_random_actress_doc(self):
        count = self.collection.count_documents({"avatar_parsed": True, "movies": {"$exists": True}})
        random_index = random.randint(0, count - 1)
        actress_doc = self.collection.find({"avatar_parsed": True}).skip(random_index).limit(1).next()
        return actress_doc

    def get_image_file_by_url(self, img_url):
        hash_name, img_name = img_url.split(':')
        img_path = os.path.join(r"\\10.16.12.105\disk\D\Pictures\J_IMG_LIB\actress", hash_name[0], img_name)
        return img_path

    def update_ui(self, actress_doc):
        pixmap = QPixmap()
        pixmap.loadFromData(self.get_image_data(actress_doc['avatar']))
        scaled_pixmap = pixmap.scaledToWidth(540, Qt.SmoothTransformation)
        self.avatar_label.setPixmap(scaled_pixmap)
        self.avatar_label.adjustSize()

        # Clear previous details
        for i in reversed(range(self.details_layout.count())):
            widget = self.details_layout.itemAt(i).widget()
            if widget != self.refresh_button:
                widget.setParent(None)

        self.details_layout.insertWidget(0, QLabel(f"Japanese Name: {actress_doc['japan_name']}"))
        self.details_layout.insertWidget(1, QLabel(f"Roman Name: {actress_doc['roman_name']}"))
        self.details_layout.insertWidget(2, QLabel(f"Publisher: {actress_doc['publisher']}"))
        self.details_layout.insertWidget(3, QLabel(f"Link: {actress_doc['link']}"))
        
        fav_button = QPushButton('Add to Favorite', self)
        
        actress_id = str(actress_doc['_id'])

        
        fav_button.clicked.connect(lambda: self.user.add_actress(actress_id, "fav_actress"))
        self.details_layout.insertWidget(4,fav_button )
        
        del_fav_button = QPushButton('Del from Favorite', self)
        del_fav_button.clicked.connect(lambda: self.user.del_actress(actress_id, "fav_actress"))
        self.details_layout.insertWidget(5,del_fav_button )
        
        hate_button = QPushButton('Add to Hate', self)
        hate_button.clicked.connect(lambda: self.user.add_actress(actress_id, "hate_actress"))
        self.details_layout.insertWidget(6,hate_button )
        

        profile = actress_doc.get('profile', {})
        for key, value in profile.items():
            self.details_layout.insertWidget(2, QLabel(f"{key}: {value}"))

        self.current_actress_movies = actress_doc.get('movies', [])

    def get_image_data(self, avatar_path):
        # This function should retrieve the image data from the given path.
        # For simplicity, we assume the image is stored locally.
        with open(self.get_image_file_by_url(avatar_path), 'rb') as f:
            return f.read()

    def show_movies_dialog(self, event):
        
        if event.button() == Qt.LeftButton:
            dialog = MovieDialog(self.current_actress_movies, self)
            dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ActressDetailApp()
    ex.show()
    sys.exit(app.exec_())