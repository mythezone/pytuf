import requests 

sessions= {}
headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

def new_session(domain):

    sessions[domain] = requests.Session()
    return sessions[domain]

def get_response_by_url(url):
    domain = url.split("/")[2]
    if domain in sessions:
        response = sessions[domain].get(url, headers=headers)
        if response.status_code == 200:
            return response 
    session = new_session(domain)
    return session.get(url)

def save_resource_by_url(url, save_path):
    response = get_response_by_url(url)
    with open(save_path, 'wb') as f:
        f.write(response.content)
    return save_path