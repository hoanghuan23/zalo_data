import sys
import os
import time
import rapidjson
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
import pandas as pd
import base64
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pytesseract
from PIL import Image
import imagehash        
from datetime import datetime
import sqlite3
import json
from openai import OpenAI
from meta_schema import META_JOB_SCHEMA, CAREER_NOTE
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from upload_image import upload_to_s3
from analyze_job import authenticate_google_sheets, formatJob
from openaitool import analyzeAndSplitJobContent, analyzeJobInformation


unique_messages = set()
processed_images = set()
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'zalo_messages.db')
group_link = ""


browser = webdriver.Chrome()
browser.get('https://chat.zalo.me')
time.sleep(30)

# ham click avatar nhom lay link nhom
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
                time.sleep(3) 
                close_button = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.modal-header-icon.icon-only")))
                close_button.click()
                return group_link
        print("Khong tim thay link nhom.")
        return ""
    except Exception as e:
        print(f"Loi khi lay link nhom Zalo: {e}")
        return ""

# lan chuot vao cac nhom khac nhau
def scroll_and_click_groups(browser, interval=20):
    try:
        groups = browser.find_elements(By.XPATH, "//div[contains(@class, 'msg-item')]")
        for group in groups:
            group.click()
            fetch_group_link()
            fetch_message_zalo()
            time.sleep(5)
    except Exception as e:
        print(f"loi")

# chống trùng lặp ảnh
def get_image_hash(filename):
    try:
        with Image.open(filename) as img:
            # Sử dụng average hash - robust hơn với các thay đổi nhỏ của ảnh
            hash = str(imagehash.average_hash(img))
            return hash
    except Exception as e:
        print(f"Lỗi khi tính hash của ảnh: {str(e)}")
        return None

# hàm trích xuất văn bản từ hình ảnh và cập nhật vào database
def extract_text_from_image(image_path):
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            width, height = img.size
            if width < 1000 or height < 1000:
                scale = max(1000/width, 1000/height)
                new_size = (int(width * scale), int(height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5) 
            
            img = img.convert('L')
            
            configs = [
                '--oem 1 --psm 3',  
                '--oem 1 --psm 6', 
                '--oem 1 --psm 11' 
            ]
            
            for config in configs:
                text_vie = pytesseract.image_to_string(img, lang='vie', config=config)
                
            # Loại bỏ khoảng trắng thừa và ký tự đặc biệt
            text_vie = ' '.join(text_vie.split())
            text_vie = ''.join(c for c in text_vie if c.isprintable())
            
            if text_vie.strip():
                print(f"Đã trích xuất được văn bản từ ảnh ({len(text_vie)} ký tự)")
            else:
                print("Không trích xuất được văn bản từ ảnh")
            
            return text_vie
    except Exception as e:
        print(f"Lỗi khi trích xuất văn bản từ hình ảnh: {str(e)}")
        return None

def append_row_to_google_sheet(service, spreadsheet_id, sheet_range, row_values):
    sheet = service.spreadsheets()
    body = {
        'values': [row_values]  # Data for a single row
    }
    result = sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range=sheet_range,
        valueInputOption='RAW',
        body=body
    ).execute()
    print(f"Successfully written {result.get('updates').get('updatedCells')} cells to Google Sheets.")


# thêm dữ liệu vào sqlite
def append_row_to_sqlite_and_sheet(values):
    columns = ["group_name", "poster", "content", "group_link", "created_at", "date", "image_url", "image_hash"]
    conn = sqlite3.connect(db_path)
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
            image_url TEXT,
            image_hash TEXT
        )
    ''')

    placeholders = ','.join(['?' for _ in values])
    cursor.execute(f'INSERT INTO zalo_messages ({" ,".join(columns)}) VALUES ({placeholders})', values)
    conn.commit()
    conn.close()
    print("Da luu vao SQLite")

    try:
        sheet_values = values[:-1]
        spreadsheet_id = '1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI'
        sheet_range = 'Sheet190!B2'
        service = authenticate_google_sheets()
        append_row_to_google_sheet(service, spreadsheet_id, sheet_range, sheet_values)
        analyze_and_update_sheet('1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI', 'Sheet190')
    except Exception as e:
        print(f"Error while pushing to Google Sheets: {e}")

#kiểm tra tin nhắn, hình ảnh đã có trong database chưa
def message_exit_data(content = None, image_hash = None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if content:
        cursor.execute("""SELECT 1 FROM zalo_messages WHERE content = ? LIMIT 1""", (content,))
    elif image_hash:
        cursor.execute("""SELECT 1 FROM zalo_messages WHERE image_hash = ? LIMIT 1""", (image_hash,))
    else:
        conn.close()
        return True
    
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
                    print("đã có tin nhắn này")
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
                            result = download_image(browser, img_url, filename)
                            if result:
                                s3_url, img_hash, extracted_text = result
                                image_urls.append((s3_url, img_hash, extracted_text))
                    except Exception as e:
                        print(f"Loi khi xu ly anh: {e}")

            if message_text or image_urls:
                if message_text:
                    unique_messages.add(message_text)
                    
                today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                today_parse = datetime.strptime(today, "%Y-%m-%d %H:%M:%S")
                created_at = int(today_parse.timestamp())
                ngay_thang_nam = datetime.now().strftime("Ngày %d Tháng %m Năm %Y")

                if image_urls:
                    for idx, (s3_url, img_hash, extracted_text) in enumerate(image_urls):
                        # Kết hợp văn bản tin nhắn và văn bản trích xuất từ ảnh
                        combined_text = message_text if idx == 0 else ""
                        if extracted_text:
                            combined_text = combined_text + "\n" + extracted_text if combined_text else extracted_text
                        
                        new_row = [group_name, user_name, combined_text, group_link, created_at, ngay_thang_nam, s3_url, img_hash]
                        append_row_to_sqlite_and_sheet(new_row)
                        print(f"Da luu anh {idx+1}: {s3_url} (text: {'co' if combined_text else 'trong'})")
                else:
                    new_row = [group_name, user_name, message_text, group_link, created_at, ngay_thang_nam, None, None]
                    append_row_to_sqlite_and_sheet(new_row)
                    print(f"Da luu tin nhan chi co text")
            
    except:
        print("loi khong the lay tin nhan")

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
        
        img_hash = get_image_hash(file_path)
        if message_exit_data(image_hash = img_hash):
            print("đã có ảnh này")
            os.remove(file_path)
            return None

        # Trích xuất văn bản từ ảnh
        extracted_text = extract_text_from_image(file_path)
        if extracted_text:
            print(f"Đã trích xuất văn bản từ ảnh: {extracted_text[:100]}...")

        s3_url = upload_to_s3(file_path)
        os.remove(file_path)

        if s3_url:
            return s3_url, img_hash, extracted_text

        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Khong the xoa file tam: {e}")

        return None

    except Exception as e:
        print(f"Loi khi tai anh: {str(e)}")
        return None

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# hàm kiểm tra dòng dữ liệu đã được phân tích chưa

# hàm phân tích và cập nhật dữ liệu vào Google Sheets
def analyze_and_update_sheet(spreadsheet_id, sheet_name):
    
    
    service = authenticate_google_sheets()

    range_name = f"{sheet_name}!C2:AA"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    if not values:
        print("Khong tim thay du lieu.")
        return
    
    for row_index, row in enumerate(values, start=2):
        if not row:
            continue
        message = row[0]
        
        processed_status = row[-1]

        if not message or processed_status == "Waiting":
            continue
        print(f"Đang phân tích tin nhắn: {row_index}")
        
        try:
            analyze_result = analyzeAndSplitJobContent(message)
            content = analyze_result.choices[0].message.content

            job_info = analyzeJobInformation(content)
            job_info_content = job_info.choices[0].message.content

            try:
                job_data = rapidjson.loads(job_info_content)
                formatted_job = formatJob(job_data)

                update_values = []

                for field in formatted_job:
                    update_values.append(field if field is not None else "")
                
                last_col = chr(ord('H') + len(update_values) - 1)
                update_ranger = f"{sheet_name}!H{row_index}:{last_col}{row_index}"
                
                body = {
                    'values': [update_values]
                }
                update_result = service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=update_ranger,
                    valueInputOption='RAW',
                    body=body
                ).execute()

                processed_status = f"{sheet_name}!AA{row_index}"
                processed_body = {
                    'values': [["Waiting"]]
                }
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=processed_status,
                    valueInputOption='RAW',
                    body=processed_body
                ).execute()

                updated_cells = update_result.get('updatedCells', 0)
                print(f"Đã cập nhật thành công dòng {row_index} với {updated_cells} ô.")
            except Exception as e:
                print(f"Lỗi khi phân tích JSON: {e}")
        except Exception as e:
            print(f"Lỗi khi phân tích dòng {row_index}: {e}")

        time.sleep(1)

def start_crawling():
    while True:
        try:
            scroll_and_click_groups(browser)
            time.sleep(5)
        except Exception as e:
            print(f"Loi khi start crawler: {e}")
            
if __name__ == "__main__":
    print("Bat dau thu thap du lieu...")
    start_crawling()
