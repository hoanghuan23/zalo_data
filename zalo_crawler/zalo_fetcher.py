# Placeholder for Zalo crawling logic
import os
import pandas as pd
import pytesseract
import base64
import requests
import json
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime
import re
import sqlite3
from datetime import datetime
from upload_image import upload_to_s3
# import warnings
# warnings.filterwarnings("ignore", category=FutureWarning)

unique_messages = set()
processed_images = set()
browser = None
group_link = ""

# hàm lấy link nhóm Zalo
def fetch_group_link():
    global group_link
    try:
        avatar_elements = browser.find_elements(By.CLASS_NAME, "threadChat__avatar.clickable")
        if avatar_elements:
            avatar_elements[0].click()
            time.sleep(1)

            link_elements = browser.find_elements(By.XPATH, '//div[@class="pi-group-profile-link__link"]')
            if link_elements:
                group_link = link_elements[0].text.strip()
                print(f"Link nhóm Zalo: {group_link}")
                time.sleep(2) 
                close_button = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.modal-header-icon.icon-only")))
                close_button.click()
                return group_link
        print("Không tìm thấy link nhóm.")
        return ""
    except Exception as e:
        print(f"Lỗi khi lấy link nhóm Zalo: {e}")
        return ""

# tự động lăn chuột vào các nhóm
def scroll_and_click_groups(browser, interval=20):
    try:
        groups = browser.find_elements(By.XPATH, "//div[contains(@class, 'msg-item')]")
        for group in groups:
            group.click()
            fetch_group_link()
            fetch_message_zalo()
            time.sleep(5)
    except Exception as e:
        print(f"Lỗi khi click vào nhóm: {e}")

# Hàm lưu dữ liệu vào file excel
def append_row_to_sqlite(values):
    columns = ["ten_nhom", "ten_nguoi_gui", "noi_dung", "link_nhom", "timestamp", "date", "link_anh"]

    conn = sqlite3.connect('zalo_messages.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zalo_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            poster TEXT,
            content TEXT,
            group_link TEXT,
            timestamp INTEGER,
            date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_url TEXT
        )
    ''')

    # Insert the new row
    placeholders = ','.join(['?' for _ in values])
    cursor.execute(f'INSERT INTO zalo_messages ({",".join(columns)}) VALUES ({placeholders})', values)
    
    conn.commit()
    conn.close()
    print("Dữ liệu đã được lưu vào SQLite database")

# Hàm thu thập tin nhắn từ Zalo
def fetch_message_zalo():
    time.sleep(15)
    try:
        chat_items = browser.find_elements(By.CLASS_NAME, 'chat-item')
        group_names = browser.find_element(By.CLASS_NAME, 'header-title')
        group_name = group_names.text.replace("&nbsp", ' ')
        print(f"Đang thu thập dữ liệu từ nhóm: {group_name}")
        global unique_messages

        for chat_item in chat_items:
            try:
                sender_name = chat_item.find_element(By.XPATH, '//div[@class="message-sender-name-content clickable"]/div[@class="truncate"]')
                user_name = sender_name.text.replace("&nbsp", ' ')
            except:
                user_name = "khong ro"

            messages = chat_item.find_elements(By.CSS_SELECTOR, '[data-component="message-text-content"]')
            images = chat_item.find_elements(By.XPATH, ".//div[@class='image-box__image']/img")
            
            if messages:
                message_text = messages[0].text
                if message_text and message_text not in unique_messages:
                    unique_messages.add(message_text)
                    thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    thoi_gian_parsed = datetime.strptime(thoi_gian, "%Y-%m-%d %H:%M:%S")
                    timestamp = int(thoi_gian_parsed.timestamp())
                    ngay_thang_nam = datetime.now().strftime("Ngày %d Tháng /%m Năm /%Y")
                    
                    new_row = [group_name, user_name, message_text, group_link, timestamp, ngay_thang_nam]
                    append_row_to_sqlite(new_row)

            # Xử lý ảnh nếu có
            if images:
                for img in images:
                    try:
                        img_url = img.get_attribute('src')
                        if img_url and img_url not in processed_images:
                            processed_images.add(img_url)
                            # Tạo tên file ngẫu nhiên với timestamp
                            filename = f"zalo_image_{int(time.time() * 1000)}.jpg"
                            # Tải và upload ảnh
                            s3_url = download_image(browser, img_url, filename)
                            if s3_url:
                                print(f"Đã xử lý ảnh: {s3_url}")
                    except Exception as e:
                        print(f"Lỗi khi xử lý ảnh: {e}")

    except Exception as e:
        print(f"Lỗi khi thu thập tin nhắn: {e}")

# hàm xử lý hình ảnh
def download_image(driver, blob_url, filename):
    try:
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)

        # Get image data using JavaScript
        js_script = """
        var blob_url = arguments[0];
        return fetch(blob_url)
            .then(response => response.blob())
            .then(blob => new Promise((resolve, reject) => {
                var reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            }));
        """
        base64_data = driver.execute_script(js_script, blob_url)
        base64_str = base64_data.split(",")[1]
        img_data = base64.b64decode(base64_str)

        # Save image to temp directory
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(img_data)
        
        # Upload to S3 and get URL
        s3_url = upload_to_s3(file_path)
        
        # Delete temp file
        os.remove(file_path)
        
        if s3_url:
            print(f"Đã tải và upload ảnh thành công: {s3_url}")
            return s3_url
        else:
            print("Lỗi khi upload ảnh lên S3")
            return None
            
    except Exception as e:
        print(f"Lỗi khi tải ảnh: {e}")
        return None

def start_crawling():
    global browser
    try:
        browser = webdriver.Chrome()
        browser.get('https://chat.zalo.me')
        time.sleep(30)  # Đợi người dùng đăng nhập
        scroll_and_click_groups(browser)
    except Exception as e:
        print(f"Lỗi khi khởi động crawler: {e}")
    finally:
        if browser:
            browser.quit()

print("Bắt đầu thu thập dữ liệu...")
