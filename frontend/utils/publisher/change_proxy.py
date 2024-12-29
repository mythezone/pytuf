import requests
import json
from pprint import pprint
import urllib.parse

def get_all_proxy_name(controller_url="http://127.0.0.1:9097", secret=None):
    endpoint = f"{controller_url}/proxies"
    headers = {'Content-Type': 'application/json'}
    
    proxies = []

    if secret:
        headers['Authorization'] = f"Bearer {secret}"

    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        proxies_list = response.json()
        # pprint(proxies)
        for key,value in proxies_list.items():
            if key == "proxies":
                for k,v in value.items():
                    if "仅海外用户" in k:
                        continue 
                    proxies.append(k)
        return proxies
    except Exception as e:
        print(f"获取当前代理时出错: {e}")
        return proxies

def switch_proxy(proxy_name, base_url=r"http://127.0.0.1:9097/proxies/%F0%9F%9A%80%20%E8%8A%82%E7%82%B9%E9%80%89%E6%8B%A9"):
    """
    切换 Clash Verge 的代理。

    :param proxy_name: 目标代理的名称（包含特殊字符或非ASCII字符时）
    :param base_url: Clash Verge 的基础URL，默认为本地地址
    :return: 布尔值，表示切换是否成功
    """
    # 对代理名称进行URL编码，以确保特殊字符正确传输
    encoded_proxy_name = urllib.parse.quote(proxy_name, safe='')

    # 构建完整的URL
    # url = f"{base_url}/proxies/{encoded_proxy_name}"

    # 设置请求头，如果需要身份验证，可以在这里添加
    headers = {
        'Content-Type': 'application/json',
        # 'Authorization': 'Bearer YOUR_SECRET'  # 如果需要，可以取消注释并设置
    }
    payload = {"name": proxy_name}
    
    try:
        # 发送PUT请求
        response = requests.put(base_url, headers=headers,json=payload)

        # 检查响应状态码
        if response.status_code == 204:
            print(f"成功切换到代理：{proxy_name}")
            return True
        else:
            print(f"切换代理失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"请求过程中出错: {e}")
        return False

if __name__ == "__main__":
    controller = " http://127.0.0.1:9097"
    secret_key = None # 如果未设置密钥，则设为 None

    current = get_all_proxy_name(controller_url=controller, secret=secret_key)
    pprint(current) 
    

    # # target = "DesiredProxyName"  # 替换为你想切换到的代理名称

    # # if current != target:
    # #     success = switch_proxy(proxy_name=target, controller_url=controller, secret=secret_key)
    # #     if success:
    # #         print(f"已成功从 {current} 切换到 {target}")
    # #     else:
    # #         print(f"切换到 {target} 失败")
    # # else:
    # #     print(f"当前代理已是 {target}，无需切换")
    # switch_proxy("(SS)E-IEPL-新加坡1")
