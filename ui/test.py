from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow
from PyQt6.QtCore import QSize, Qt 

import sys 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("My App")
        
        self.button_is_checked =True 
        
        self.button = QPushButton("Press Me!")
        self.button.setCheckable(True)
        self.button.clicked.connect(self.the_button_was_clicked)
        self.button.clicked.connect(self.the_button_was_toggled)
        self.button.released.connect(self.the_button_was_released)
        self.button.setChecked(self.button_is_checked)
        
        self.setFixedSize(QSize(400,300))
        
        self.setCentralWidget(self.button)
        
    def the_button_was_clicked(self):
        self.button.setText("You already clicked me!")
        print("Clicked!")
        self.button.setEnabled(False)
        self.setWindowTitle("My Oneshot App")
        
    def the_button_was_toggled(self,checked):
        self.button_is_checked = checked
        print("Checked?",self.button_is_checked)
                
                
    def the_button_was_released(self):
        self.button_is_checked = self.button.isChecked()
        print(self.button_is_checked)

app = QApplication(sys.argv)


window = MainWindow()
window.show()


app.exec()