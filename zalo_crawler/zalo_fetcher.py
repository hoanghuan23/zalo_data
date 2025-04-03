# Placeholder for Zalo crawling logic
import os
import pandas as pd
import base64
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime
import sqlite3
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from upload_image import upload_to_s3

unique_messages = set()
processed_images = set()
browser = None
group_link = ""

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
                print(f"Link nhom Zalo: {group_link}")
                time.sleep(2) 
                close_button = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.modal-header-icon.icon-only")))
                close_button.click()
                return group_link
        print("Khong tim thay link nhom.")
        return ""
    except Exception as e:
        print(f"Loi khi lay link nhom Zalo: {e}")
        return ""

def scroll_and_click_groups(browser, interval=20):
    try:
        while True:
            groups = browser.find_elements(By.XPATH, "//div[contains(@class, 'msg-item')]")
            for i, group in enumerate(groups):
                try:
                    browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", group)
                    
                    WebDriverWait(browser, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"(//div[contains(@class, 'msg-item')])[{i+1}]"))
                    )
                    
                    try:
                        group.click()
                    except:
                        browser.execute_script("arguments[0].click();", group)
                    
                    print(f"Click thành công nhóm {i+1}")

                    fetch_group_link()
                    fetch_message_zalo()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Không thể click nhóm thứ {i + 1}")
                    continue
    except Exception as e:
        print(f"Lỗi ngoài vòng lặp: {e}")

# thêm dữ liệu vào sqlite
def append_row_to_sqlite(values):
    columns = ["group_name", "poster", "content", "group_link", "created_at", "date", "image_url"]
    conn = sqlite3.connect('zalo_messages.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS zalo_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            poster TEXT,
            content TEXT,
            group_link TEXT,
            created_at TEXT,
            date TEXT,
            image_url TEXT
        )
    ''')

    placeholders = ','.join(['?' for _ in values])
    cursor.execute(f'INSERT INTO zalo_messages ({" ,".join(columns)}) VALUES ({placeholders})', values)
    conn.commit()
    conn.close()
    print("Da luu vao SQLite")

#kiểm tra tin nhắn đã có trong database chưa
def message_exit_data(content):
    conn = sqlite3.connect('zalo_messages.db')
    cursor = conn.cursor()
    cursor.execute("""SELECT 1 FROM zalo_messages WHERE content = ? LIMIT 1""", (content,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def fetch_message_zalo():
    time.sleep(5)
    try:
        chat_items = browser.find_elements(By.CLASS_NAME, 'chat-item')
        group_names = browser.find_element(By.CLASS_NAME, 'header-title')
        group_name = group_names.text.replace("&nbsp", ' ')

        for chat_item in chat_items:
            try:
                sender_name = chat_item.find_element(By.XPATH, '//div[@class="message-sender-name-content clickable"]/div[@class="truncate"]')
                user_name = sender_name.text.replace("&nbsp", ' ')
            except:
                user_name = "khong ro"

            message_text = ""
            messages = chat_item.find_elements(By.CSS_SELECTOR, '[data-component="message-text-content"]')
            if messages:
                message_text = messages[0].text

            # Kiểm tra tin nhắn trùng lặp
            if message_text:
                if message_exit_data(message_text):
                    continue

            image_urls = []
            images = chat_item.find_elements(By.XPATH, ".//div[@class='image-box__image']/img")
            if images:
                for img in images:
                    try:
                        img_url = img.get_attribute('src')
                        if img_url:
                            if img_url in processed_images:
                                continue
                                
                            processed_images.add(img_url)
                            filename = f"zalo_image_{int(time.time() * 1000)}.jpg"
                            s3_url = download_image(browser, img_url, filename)
                            if s3_url:
                                image_urls.append(s3_url)
                    except Exception as e:
                        print(f"Loi khi xu ly anh: {e}")

            if message_text or image_urls:
                if message_text:
                    unique_messages.add(message_text)
                    
                today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                today_parse = datetime.strptime(today, "%Y-%m-%d %H:%M:%S")
                created_at = int(today_parse.timestamp())
                ngay_thang_nam = datetime.now().strftime("Ngay %d Thang /%m Nam /%Y")

                if image_urls:
                    for idx, s3_url in enumerate(image_urls):
                        row_text = message_text if idx == 0 else ""
                        new_row = [group_name, user_name, row_text, group_link, created_at, ngay_thang_nam, s3_url]
                        append_row_to_sqlite(new_row)
                        print(f"Da luu anh {idx+1}: {s3_url} (text: {'co' if row_text else 'trong'})")
                else:
                    new_row = [group_name, user_name, message_text, group_link, created_at, ngay_thang_nam, None]
                    append_row_to_sqlite(new_row)
                    print(f"Da luu tin nhan chi co text")

    except Exception as e:
        print(f"Loi khi fetch tin nhan: {str(e)}")

def download_image(driver, blob_url, filename):
    try:
        if not blob_url:
            print("URL anh khong hop le")
            return None

        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)

        print(f"Dang tai anh tu URL: {blob_url}")

        js_script = """
        var blob_url = arguments[0];
        return fetch(blob_url)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.blob();
            })
            .then(blob => new Promise((resolve, reject) => {
                var reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            }));
        """

        try:
            base64_data = driver.execute_script(js_script, blob_url)
            if not base64_data:
                print("Khong the lay du lieu anh")
                return None

            base64_str = base64_data.split(",")[1]
            img_data = base64.b64decode(base64_str)
            file_path = os.path.join(temp_dir, filename)

            with open(file_path, 'wb') as f:
                f.write(img_data)

            if not os.path.exists(file_path):
                print("Khong the luu file anh tam")
                return None

            s3_url = upload_to_s3(file_path)

            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Khong the xoa file tam: {e}")

            return s3_url

        except Exception as e:
            print(f"Loi xu ly JS: {str(e)}")
            return None

    except Exception as e:
        print(f"Loi khi tai anh: {str(e)}")
        return None

def start_crawling():
    while True:
        global browser
        try:
            browser = webdriver.Chrome()
            browser.get('https://chat.zalo.me')
            time.sleep(30)
            scroll_and_click_groups(browser)
        except Exception as e:
            print(f"Loi khi start crawler: {e}")

if __name__ == "__main__":
    print("Bat dau thu thap du lieu...")
    start_crawling()
