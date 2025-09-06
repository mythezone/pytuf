import requests

from typing import List, Dict


with open("/Volumes/local/Project/python/pytuf/script/cookies.txt", "r") as f:
    cookies = f.read()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Cookie": cookies,
}


def html_to_file(url: str, filename: str):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text)
    else:
        print(f"Failed to retrieve page: {url} with status code {response.status_code}")


if __name__ == "__main__":
    test_url = "https://javdb561.com/actors/MkAX"
    html_to_file(test_url, "test.html")
