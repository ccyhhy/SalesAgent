# config_example.py
# 这是配置模板，使用时请重命名为 config.py 并填入真实信息

# ================= AI 配置 =================
API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxx"  # 在这里填入你的 Key
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen-plus"

# ================= 代理配置 =================
# 隧道代理配置 (青果/快代理)
PROXY_HOST = "tun-uzqqwl.qg.net"
PROXY_PORT = "16277"
PROXY_USER = "YOUR_USERNAME"  # 填入用户名
PROXY_PASS = "YOUR_PASSWORD"  # 填入密码

# ================= 文件路径 =================
INPUT_FILE = "leads.xlsx"
OUTPUT_FILE = "leads_analyzed.xlsx"
SOP_FILE = "sop.txt"

# ================= 爬虫配置 =================
SEARCH_ENGINE_URL = "https://www.baidu.com/s?wd="
MIN_SLEEP = 2.0
MAX_SLEEP = 5.0
PAGE_WAIT_MIN = 3.0
PAGE_WAIT_MAX = 6.0