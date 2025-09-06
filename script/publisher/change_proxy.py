import requests
from typing import Dict, List, Optional
from pprint import pprint
from urllib.parse import quote


def _headers(secret: Optional[str] = None) -> Dict[str, str]:
    h = {'Content-Type': 'application/json'}
    if secret:
        h['Authorization'] = f"Bearer {secret}"
    return h


def _get_proxies(controller_url: str = "http://127.0.0.1:9097", secret: Optional[str] = None) -> Dict:
    resp = requests.get(f"{controller_url.rstrip('/')}/proxies", headers=_headers(secret), timeout=5)
    resp.raise_for_status()
    return resp.json() or {}


def _pick_selector_group(proxies_json: Dict, preferred: Optional[str] = None) -> Optional[str]:
    proxies = proxies_json.get('proxies') or {}
    if preferred and preferred in proxies:
        return preferred
    # Common selector group names in Clash/Verge
    candidates = [
        'GLOBAL',
        '♻️ 自动选择', '自动选择',
        '🔰 节点选择', '🚀 节点选择', '节点选择',
        'PROXY', 'Proxy', '代理', '手动选择',
    ]
    for name in candidates:
        if name in proxies:
            return name
    # Fallback: first selector-like group (has 'all' list)
    for name, info in proxies.items():
        if isinstance(info, dict) and isinstance(info.get('all'), list):
            return name
    return None


def get_all_proxy_name(
    controller_url: str = "http://127.0.0.1:9097",
    secret: Optional[str] = None,
    group_name: Optional[str] = None,
) -> List[str]:
    """Return node names from the selected proxy group (selector)."""
    try:
        data = _get_proxies(controller_url, secret)
        proxies = data.get('proxies') or {}
        group = _pick_selector_group(data, preferred=group_name)
        if not group:
            return []
        info = proxies.get(group) or {}
        nodes = info.get('all') or []
        # Filter out special entries if necessary
        return [n for n in nodes if n and '仅海外用户' not in n]
    except Exception as e:
        print(f"获取代理列表出错: {e}")
        return []


def switch_proxy(
    proxy_name: str,
    *,
    controller_url: str = "http://127.0.0.1:9097",
    secret: Optional[str] = None,
    group_name: Optional[str] = None,
) -> bool:
    """Switch Clash selector group to the specified node.

    Tries standard Clash endpoint: PUT /proxies/{group} {"name": proxy_name}
    Falls back to POST /proxies/{group}/select when required by some builds.
    """
    try:
        data = _get_proxies(controller_url, secret)
        group = _pick_selector_group(data, preferred=group_name)
        if not group:
            print("未找到可用的选择器分组 (selector group)")
            return False
        base = controller_url.rstrip('/')
        h = _headers(secret)
        # Standard Clash API
        url_put = f"{base}/proxies/{quote(group, safe='')}"
        payload = {"name": proxy_name}
        r = requests.put(url_put, headers=h, json=payload, timeout=5)
        if r.status_code == 204:
            print(f"成功切换到代理：{proxy_name} (组: {group})")
            return True
        # Fallback endpoint used by some forks
        url_post = f"{base}/proxies/{quote(group, safe='')}/select"
        r2 = requests.post(url_post, headers=h, json=payload, timeout=5)
        if r2.status_code in (200, 204):
            print(f"成功切换到代理：{proxy_name} (组: {group})")
            return True
        print(f"切换代理失败，状态码: {r.status_code}/{r2.status_code}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"请求过程中出错: {e}")
        return False


if __name__ == "__main__":
    controller = "http://127.0.0.1:9097"
    secret_key = None  # 如果未设置密钥，则设为 None
    group = None       # 可指定 group，例如 'GLOBAL' 或 '🔰 节点选择'

    nodes = get_all_proxy_name(controller_url=controller, secret=secret_key, group_name=group)
    print("可用节点数:", len(nodes))
    pprint(nodes[:20])
    if nodes:
        switch_proxy(nodes[0], controller_url=controller, secret=secret_key, group_name=group)
