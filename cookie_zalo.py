import json
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
debug_port = "--remote-debugging-port=9222"
user_data_dir = r'--user-data-dir=C:/Chrome_dev'

subprocess.Popen([chrome_path, debug_port, user_data_dir])
time.sleep(2)

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)

driver.get("https://chat.zalo.me/")
time.sleep(10)  # Đợi người dùng đăng nhập thủ công

# # Lưu cookie vào file
# cookies = driver.get_cookies()
# with open("zalo_cookies.json", "w", encoding='utf-8') as f:
#     json.dump(cookies, f, indent=4, ensure_ascii=False)

# print("✅ Đã lưu cookie thành công vào 'zalo_cookies.json'")

# driver.quit()
