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
import subprocess
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
from openaitool import analyzeAndSplitJobContent, analyzeJobInformation, analysisPostType
from detail_job import update_job_row_by_row
from test_push_job_elasticsearch import read_data_from_sheet

unique_messages = set()
processed_images = set()
db_path = os.path.abspath("zalo_messages.db")
group_link = ""

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
debug_port = "--remote-debugging-port=9222"
user_data_dir = r'--user-data-dir=C:/Chrome_dev'
subprocess.Popen([chrome_path, debug_port, user_data_dir])

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress","127.0.0.1:9222")
browser = webdriver.Chrome(options=chrome_options)
browser = webdriver.Chrome()
browser.get('https://chat.zalo.me')
time.sleep(15)

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

            time.sleep(10)
    except Exception as e:
        print(f"loi" + {e})

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

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_text_from_image(image_path):
    try:
        base64_image = encode_image(image_path)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Đọc toàn bộ nội dung văn bản chỉ có trong hình ảnh này bằng tiếng Việt, không thêm bất kỳ câu văn AI nào, không thêm tiêu đề, không thêm ký tự |. Chỉ trả lại đúng phần văn bản gốc của ảnh dưới dạng đoạn văn."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]   
                }
            ],
        )
        
        result = response.choices[0].message.content.strip()
        return result

    except Exception as e:
        print(f"Lỗi khi trích xuất nội dung ảnh: {str(e)}")
        return None
    
def append_row_to_google_sheet(service, row_values):
    sheet = service.spreadsheets()
    body = {
        'values': [[""] + row_values]
    }
    result = sheet.values().append(
        spreadsheetId= '1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI',
        range='ĐƠN HÀNG PHÂN TÍCH!A2:B',
        valueInputOption='RAW',
        body=body
    ).execute()
    print(f"Đã ghi thành công {result.get('updates').get('updatedCells')} cells to Google Sheets.")


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
        service = authenticate_google_sheets()
        append_row_to_google_sheet(service, sheet_values)
        analyPostType()
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
                # sender_name = chat_item.find_element(By.XPATH, '//div[@class="message-sender-name-content clickable"]/div[@class="truncate"]')
                sender_name_element = chat_item.find_element(By.CSS_SELECTOR, ".message-sender-name-content .truncate")
                
                if sender_name_element:
                    user_name = sender_name_element[0].text.replace("&nbsp", ' ')
                    last_user_name = user_name
                else:
                    user_name = last_user_name
            except:
                user_name = "khong ro"

            message_text = ""
            messages = chat_item.find_elements(By.CSS_SELECTOR, '[data-component="message-text-content"]')
            if messages:
                message_text = messages[0].text
            
            now = datetime.now()
            last_time_push = None

            time_element = chat_item.find_elements(By.CSS_SELECTOR, '.card-send-time__sendTime')
            if time_element:
                last_time_push = time_element[0].text
                print(f"Thoi gian tin nhan: {last_time_push}")
            
            if not last_time_push:
                continue

            h, m = map(int, last_time_push.split(':'))
            created_at = int(now.replace(hour=h, minute=m, second=0, microsecond=0).timestamp())
            ngay_thang_nam = now.strftime("Ngày %d Tháng %m Năm %Y")

            # Kiểm tra tin nhắn trùng lặp
            if message_text:
                if message_exit_data(message_text):
                    print("đã có tin nhắn này")
                    continue

            image_urls = []
            # images = chat_item.find_elements(By.XPATH, "//div[contains(@class, 'img-center-box')]//img")
            images = chat_item.find_elements(By.CSS_SELECTOR, ".img-center-box img")
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

                if image_urls:
                    for idx, (s3_url, img_hash, extracted_text) in enumerate(image_urls):                        
                        new_row = [group_name, user_name, extracted_text, group_link, created_at, ngay_thang_nam, s3_url, img_hash]
                        append_row_to_sqlite_and_sheet(new_row)
                        print(f"Da luu anh {idx+1}: {s3_url} (text: {'co' if extracted_text else 'trong'})")
                else:
                    new_row = [group_name, user_name, message_text, group_link, created_at, ngay_thang_nam, None, None]
                    append_row_to_sqlite_and_sheet(new_row)
                    print(f"Da luu tin nhan chi co text")
    except Exception as e:
        print(f"loi khong the lay tin nhan zalo: {e}")

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
    
def get_column_letter(col_index):
    letter = ""
    while col_index > 0:
        col_index, remainder = divmod(col_index - 1, 26)
        letter = chr(65 + remainder) + letter
    return letter

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyPostType():
    service = authenticate_google_sheets()
    spreadsheet_id = '1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI'
    sheet_name = 'Sunrise'
    read_range = f"{sheet_name}!D2:K"

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=read_range
        ).execute()

        values = result.get('values', [])
        if not values:
            print("Không tìm thấy dữ liệu.")
            return

        for idx, row in enumerate(values, start=2):
            if not row or not row[0]:
                continue

            raw_text = row[0]
            
            if len(row) > 7 and row[7]:
                continue

            try:
                analysis = analysisPostType(raw_text)
                post_type_raw = analysis.choices[0].message.content
                post_type_data = rapidjson.loads(post_type_raw)

                write_range = f"'{sheet_name}'!K{idx}"
                body = {'values': [[post_type_data['postType']]]}
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=write_range,
                    valueInputOption='RAW',
                    body=body
                ).execute()

                col_h_value = row[4] if len(row) > 4 else ""
 
                print(f"Dòng {idx}: Đã ghi phân loại: {post_type_data['postType']}")

                if post_type_data['postType'] == 'TIN RÁC' or not col_h_value:
                    nopush = f"{sheet_name}!A{idx}"
                    a_body = {
                        'values': [["INVALIDS"]]
                    }
                    service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=nopush,
                        valueInputOption='RAW',
                        body=a_body
                    ).execute()

                if post_type_data['postType'] == 'VIỆC LÀM NHẬT' and col_h_value:
                    analyze_and_update_sheet(spreadsheet_id, sheet_name, idx)
                    # read_data_from_sheet()

            except Exception as e:
                print(f"Lỗi phân tích dòng {idx}: {e}")

    except Exception as e:
        print(f"Lỗi khi truy cập Google Sheet: {e}")

# hàm phân tích và cập nhật dữ liệu vào Google Sheets
def analyze_and_update_sheet(spreadsheet_id, sheet_name, row_index):
    service = authenticate_google_sheets()

    # đọc dữ liệu cột nội dung D và trạng thái AE
    range_name = f"{sheet_name}!D{row_index}:AE{row_index}"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    if not values:
        print("Khong tim thay du lieu.")
        return
    
    for row_index, row in enumerate(values, start=row_index):
        if not row:
            continue
        message = row[0]
        
        processed_status = row[-1]

        if not message or processed_status == "ZALO":
            continue
        print(f"Đang phân tích tin nhắn: {row_index}")
        
        try:
            analyze_result = analyzeAndSplitJobContent(message)
            content = analyze_result.choices[0].message.content

            job_info = analyzeJobInformation(content)
            job_info_content = job_info.choices[0].message.content

            # print(f"job_info_content: {job_info_content}")
            try:
                job_data = rapidjson.loads(job_info_content)
                # print(job_data)
                formatted_job = formatJob(job_data)
                print(f"Đã phân tích {formatted_job}")

                columnI = [f"=image(h{row_index})"]
                update_values = [content]

                for field in formatted_job:
                    update_values.append(field if field is not None else "")

                update_values = columnI + update_values[:5] + [""] + update_values[5:]

                start_col_index = ord('I') - 64
                last_col_index = start_col_index + len(update_values) - 1
                last_col = get_column_letter(last_col_index)
                update_ranger = f"{sheet_name}!I{row_index}:{last_col}{row_index}"
                body = {
                    'values': [update_values]
                }
                update_result = service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=update_ranger,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()

                zalo_status = f"{sheet_name}!AF{row_index}"
                zalo_body = {
                    'values': [["ZALO"]]
                }
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=zalo_status,
                    valueInputOption='RAW',
                    body=zalo_body
                ).execute()
                
                # matching giữa visa và việc làm AI để cho ra việc làm phân tích
                job = update_job_row_by_row(row_index)
                job_status = f"{sheet_name}!O{row_index}"
                job_body = {
                    'values': [[job]]
                }
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=job_status,
                    valueInputOption='RAW',
                    body=job_body
                ).execute()

                updated_cells = update_result.get('updatedCells', 0)
                print(f"Đã cập nhật thành công dòng {row_index} với {updated_cells} ô.")
            except Exception as e:
                print(f"Lỗi khi phân tích JSON: {e}")
        except Exception as e:
            print(f"Lỗi khi phân tích dòng {row_index}: {e}")

        time.sleep(1)

def start_crawling():
    refresh_interval = 120 * 60  # 10 phút
    last_refresh = time.time()
    while True:
        try:
            current_time = time.time()
            if current_time - last_refresh > refresh_interval:
                print("Đang làm mới trình duyệt...")
                browser.refresh()
                time.sleep(5)
                last_refresh = current_time
            scroll_and_click_groups(browser)
            time.sleep(5)
        except Exception as e:
            print(f"Loi khi start crawler: {e}")
            
if __name__ == "__main__":
    print("Bat dau thu thap du lieu...")
    # start_crawling()
    analyPostType()
