from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pickle
from google.oauth2 import service_account
from googleapiclient.discovery import build

driver = webdriver.Chrome()
url = "https://www.facebook.com/"
driver.get(url)

cookies = pickle.load(open("facebook_cookies_02.pkl", "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)
driver.refresh()
time.sleep(3)

group_url = "https://www.facebook.com/groups/feed/"
driver.get(group_url)
print("Đã tải xong")
time.sleep(2)

ten_nhom_tim_kiem = "tokutei"
nd_01 = ""
nd_02 = ""

search_input = driver.find_element(By.XPATH, "//input[@placeholder='Tìm kiếm nhóm']")
search_input.send_keys(ten_nhom_tim_kiem)
search_input.send_keys(Keys.RETURN)
time.sleep(3)

count = 0
so_nhom = 500
urls_lay_duoc = set()

def scroll_to_element(element):
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
    time.sleep(1)

creds = service_account.Credentials.from_service_account_file('v.json')
service = build('sheets', 'v4', credentials=creds)
spreadsheet_id = '10SL6WCt6YPrHUtxzVmsNI1futs-SOi9ebYIn_C641vc'
sheet_name = 'Nhóm kỹ sư mới'

def add_header_to_sheet():
    header = [['Tên nhóm', 'URL nhóm', 'Thông tin nhóm']]
    range_name = f'{sheet_name}!A1:C1'  
    body = {
        'values': header
    }
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()

add_header_to_sheet()

def save_to_google_sheet(data):
    range_name = f'{sheet_name}!A2:C'
    body = {
        'values': data
    }

    retries = 3  
    for attempt in range(retries):
        try:
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            print("Data saved successfully")
            break  
        except Exception as e:
            print(f"Error saving data to Google Sheets (Attempt {attempt + 1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                time.sleep(5)  
            else:
                print("Max retries reached. Could not save data.")

def get_existing_urls():
    range_name = f'{sheet_name}!B2:B'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    existing_urls = [row[0] for row in result.get('values', [])]

    return set(existing_urls)

data_to_save = []

existing_urls = get_existing_urls()

while count < so_nhom:
    div_elements = driver.find_elements(By.CSS_SELECTOR, 'div.x1obq294.x5a5i1n.xde0f50.x15x8krk.x1lliihq')
    # div_elements = driver.find_elements(By.CSS_SELECTOR, 'div.x193iq5w.x1xwk8fm')
    if not div_elements:
        print("Không tìm thấy thẻ div cần cuộn.")
        break

    for div_element in div_elements[count:]:
        try:
            ten_nhom = ""
            url_nhom = ""
            thong_tin_nhom = ""

            url_bai_viet_elem = WebDriverWait(div_element, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="x78zum5 xdt5ytf xz62fqu x16ldp7u"]'))
            )
            time.sleep(1)

            try:
                url_nhom_elem = url_bai_viet_elem.find_element(By.CSS_SELECTOR, 'a[aria-hidden="true"]')
                url_nhom = url_nhom_elem.get_attribute('href')
            except Exception as e:
                url_nhom = ""

            if url_nhom in existing_urls:
                print(f"Link nhóm {url_nhom} đã có trong Google Sheets, bỏ qua.")
                count += 1
                continue  

            try:
                thong_tin_nhom_elem = url_bai_viet_elem.find_element(By.CSS_SELECTOR, 'span[class="x1lliihq x6ikm8r x10wlt62 x1n2onr6"]')
                thong_tin_nhom = thong_tin_nhom_elem.text
            except Exception as e:
                thong_tin_nhom = ""

            try:
                ten_nhom_elem = url_bai_viet_elem.find_element(By.CSS_SELECTOR, 'a[aria-hidden="true"]')
                ten_nhom = ten_nhom_elem.text
                if nd_01.lower() not in ten_nhom.lower() or nd_02.lower() not in ten_nhom.lower():
                # if nd_01.lower() not in ten_nhom.lower():
                    ten_nhom = ""
                    thong_tin_nhom = ""
                    url_nhom = ""
            except Exception as e:
                ten_nhom = ""

            print(f"STT: {count+1}")
            print(f"Tên nhóm: {ten_nhom}")
            print(f"URL nhóm: {url_nhom}")
            print(f"Thông tin nhóm: {thong_tin_nhom}")
            print("-"*40)
            time.sleep(1)

            scroll_to_element(url_bai_viet_elem)

            if url_nhom:
                existing_urls.add(url_nhom) 

            if ten_nhom and url_nhom and thong_tin_nhom:
                data_to_save.append([ten_nhom, url_nhom, thong_tin_nhom])
                save_to_google_sheet(data_to_save)
                print(f"Đã lưu nhóm {ten_nhom} vào Google Sheets.")
               
        except Exception as e:
            print(f"Lỗi khi lấy thông tin từ bài viết {count + 1}: {str(e)}")

        count += 1
        if count >= so_nhom:
            break

# if data_to_save:
#     save_to_google_sheet(data_to_save)
#     print(f"Đã lưu nhóm {ten_nhom} nhóm vào Google Sheets.")
driver.quit()