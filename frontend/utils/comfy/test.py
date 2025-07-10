import requests
import time
import json 

# ComfyUI 服务器地址
COMFYUI_URL = "http://10.16.10.62:8189"

# 加载你的工作流数据（你也可以直接使用上面的JSON）
with open("./utils/comfy/Patty_ill.json", "r", encoding="utf-8") as f:
    workflow = json.load(f)
    
workflow["prompt"] = "A beautiful landscape with mountains and a river, in the style of a watercolor painting."

# 提交工作流
response = requests.post(f"{COMFYUI_URL}/prompt", json=workflow)
# assert response.status_code == 200
print("工作流提交成功，正在获取结果...")
if response.status_code != 200:
    print(f"提交工作流失败: {response.status_code}, {response.text}")
    exit(1)
prompt_id = response.json()["prompt_id"]

# 轮询获取结果
while True:
    r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
    if r.status_code == 200 and r.json().get("outputs"):
        break
    time.sleep(1)

outputs = r.json()["outputs"]
# 提取图像路径
image_info = list(outputs.values())[0]["images"][0]
filename = image_info["filename"]
subfolder = image_info["subfolder"]

# 下载图像
img_response = requests.get(
    f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}"
)

with open("output.png", "wb") as f:
    f.write(img_response.content)
print("图片已保存为 output.png")
