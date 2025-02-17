from bs4 import BeautifulSoup
import requests

class Page:
    def __init__(self,url):
        self.url = url
        self.init()

    def init(self):
        self.response = requests.get(self.url)
        self.status_code = self.response.status_code
        self.soup = BeautifulSoup(self.response.text, 'html.parser')
    
    def get_one_element_by_css_selector(self,selector):
        return self.soup.select_one(selector)
    
    def get_all_elements_by_css_selector(self,selector):
        return self.soup.select(selector)
    
    