from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import pickle
import os
import pandas as pd
from datetime import datetime, timedelta
import pytesseract
from PIL import Image
import requests
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build


def extract_text_from_image(image_url):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        text = pytesseract.image_to_string(img, lang='vie')
        text = text.replace("\n", " ")

        return text.strip()
    except Exception as e:
        print(f"Lỗi xử lý ảnh: {e}")

def tinh_thoi_gian(thoi_gian_text):
    try:
        weekday_mapping = {
            "Thứ Hai": "Monday",
            "Thứ Ba": "Tuesday",
            "Thứ Tư": "Wednesday",
            "Thứ Năm": "Thursday",
            "Thứ Sáu": "Friday",
            "Thứ bảy": "Saturday",
            "Chủ Nhật": "Sunday",
        }
        for vietnamese, english in weekday_mapping.items():
            if vietnamese in thoi_gian_text:
                thoi_gian_text = thoi_gian_text.replace(vietnamese, english)
                break
        processed_string = thoi_gian_text.replace(
            "Tháng ", "").replace("lúc ", "")
        return datetime.strptime(processed_string, "%A, %d %m, %Y %H:%M")
    except Exception as e:
        print(f"Lỗi khi chuyển đổi chuỗi thời gian: {str(e)}")
        return None

# def save_to_excel(data, directory="Bài viết/Nhật Bản/TC/11-7"):
#     thoi_gian_ht = datetime.now()
#     ten_file_excel = f"nhom_01_{thoi_gian_ht.strftime('%Y-%m-%d %H-%M-%S').replace(' ', '-')}.xlsx"
#     if not os.path.exists(directory):
#         os.makedirs(directory)
#     filepath = os.path.join(directory, ten_file_excel)
#     df = pd.DataFrame(data)
#     df.to_excel(filepath, index=False)
#     print(f"Dữ liệu đã được lưu vào tệp {filepath}.")

def save_to_gg_sheet(data, spreadsheet_id, sheet_name):
    try:
        service = build('sheets', 'v4', credentials=creds)
        body = {
            'values': [list(item.values()) for item in data]
        }
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f'{sheet_name}!A2',
            valueInputOption='RAW',
            body=body
        ).execute()
        print(f"{result.get('updates').get('updatedCells')} cells updated.")
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu vào Google Sheets: {str(e)}")

# Hàm kiểm tra trùng lặp nội dung
def check_duplicate_content(noi_dung, spreadsheet_id, sheet_name):
    try:
        service = build('sheets', 'v4', credentials=creds)
        range_name = f'{sheet_name}!B2:B'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        for row in values:
            if row and row[0] == noi_dung:
                return True
        return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra trùng lặp nội dung: {str(e)}")
        return False

driver = webdriver.Chrome()
url = "https://www.facebook.com/"
driver.get(url)

cookies = pickle.load(open("facebook_cookies_02.pkl", "rb"))
for cookie in cookies:
    driver.add_cookie(cookie)
driver.refresh()

url_profiles = "https://www.facebook.com/profile.php?id="

creds = service_account.Credentials.from_service_account_file('update_dulieu.json')
service = build('sheets', 'v4', credentials=creds)

spreadsheet_id = '10SL6WCt6YPrHUtxzVmsNI1futs-SOi9ebYIn_C641vc'
sheet_name = 'Nhóm Tokutei'
range_name = f'{sheet_name}!B2:B'
result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
values = result.get('values', [])   

tu_hang = 51
den_hang = 80

for i, row in enumerate(values[tu_hang-2:den_hang-1], start=tu_hang):  
    driver.get(row[0] + "?sorting_setting=CHRONOLOGICAL")
    print(f"Đã tải xong nhóm: {row[0]}")
    time.sleep(3)

    count = 0
    groups_data = []
    flag = False
    # ten_nhom = driver.find_element(
    #     By.CSS_SELECTOR, 'span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1lliihq.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1ill7wo.x41vudc.x1q74xe4.xyesn5m.x1xlr1w8.xzsf02u.x1yc453h a').text
    ten_nhom = driver.find_element(By.XPATH,"//div[@class='x1e56ztr x1xmf6yo']//h1//span//a").text
    print(f"Tên nhóm: {ten_nhom}")

    while True:
        div_elements = driver.find_elements(By.CSS_SELECTOR, 'div[aria-posinset]')
        if not div_elements:
            print("Không tìm thấy thẻ div cần cuộn.")
            break

        for div_element in div_elements[count:]:
            try:
                allLinksInBlock=div_element.find_elements(By.CSS_SELECTOR, 'a[role="link"]')
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", allLinksInBlock[0])
                ten_nguoi_dung = ""
                url_nguoi_dung = ""
                noi_dung = ""
                so_comment = ""
                url_profile = ""

                url_bai_viet_elem = None
                pattern = r"https://www\.facebook\.com/groups/.+/user/"
                patternFacebookLink = r"https://www\.facebook\.com/groups/"
                for link in allLinksInBlock:
                    href = link.get_attribute("href")
                    if not re.search(pattern, link.get_attribute("href")) and re.search(patternFacebookLink, link.get_attribute("href")) and not url_bai_viet_elem:
                        url_bai_viet_elem = link
                
                try:
                    ten_nguoi_dung_elm=div_element.find_element(By.CSS_SELECTOR, '[data-ad-rendering-role="profile_name"]')
                    ten_nguoi_dung =ten_nguoi_dung_elm.text
                    if ten_nguoi_dung!="Người tham gia ẩn danh":
                        url_nguoi_dung=ten_nguoi_dung_elm.find_element(By.CSS_SELECTOR, 'a[role="link"]').get_attribute("href")
                        pattern = r"/user/(\d+)"
                        match = re.search(pattern, url_nguoi_dung)
                        if match:
                            url_profile= url_profiles+match.group(1)
                except Exception as e:
                    ten_nguoi_dung = ""


                # time.sleep(2000)

                action = ActionChains(driver)
                action.move_to_element(url_bai_viet_elem).perform()
                time.sleep(2)

                try:
                    # thoi_gian = driver.find_element(
                    #     By.CSS_SELECTOR, 'span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1nxh6w3.x1sibtaa.xo1l8bm.xzsf02u').text
                    thoigianElm=driver.find_element(
                        By.CSS_SELECTOR, '.__fb-light-mode div[role="tooltip"],.__fb-dark-mode div[role="tooltip"]')
                    thoi_gian = thoigianElm.text
                except Exception as e:
                    thoi_gian = ""
                thoi_gian_text = thoi_gian

                if thoi_gian:
                    thoi_gian_parsed = tinh_thoi_gian(thoi_gian)
                    thoi_gian = int(thoi_gian_parsed.timestamp())
                    if thoi_gian_parsed and int(thoi_gian_parsed.timestamp()) <= 1753117200:
                        flag = True
                        break
                else:
                    thoi_gian_parsed = ""

                action = ActionChains(driver)
                action.key_down(Keys.CONTROL).click(
                    url_bai_viet_elem).key_up(Keys.CONTROL).perform()
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(5)
                url_bai_viet = driver.current_url

                try:

                    content_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.__fb-light-mode [role="dialog"] [role="dialog"],div.__fb-dark-mode [role="dialog"] [role="dialog"]'))
                    )

                    try:
                        noi_dung_elem = content_element.find_element(By.CSS_SELECTOR, '[data-ad-rendering-role="story_message"]')
                        noi_dung=noi_dung_elem.text
                        print("Nội dung:", {noi_dung})
                    except Exception as e:
                        noi_dung = ""
                    if not noi_dung:
                        try:
                            noi_dung_elem = content_element.find_elements(By.CSS_SELECTOR, '[data-ad-rendering-role="story_message"]')
                            if len(noi_dung_elem) == 1:
                                noi_dung = noi_dung_elem[0].text
                                print("1.1")
                            elif len(noi_dung_elem) > 1:
                                noi_dung = noi_dung_elem[0].text
                                print("1.9")
                            else:
                                noi_dung_elem_1 = content_element.find_elements(By.CSS_SELECTOR, 'div.xdj266r.x11i5rnm.xat24cr.x1mh8g0r.x1vvkbs.x126k92a div')
                                noi_dung = " ".join([element.text for element in noi_dung_elem_1])
                                print("1.2")
                        except Exception as e:
                            noi_dung = ""

                    if not noi_dung:
                        try:
                            noi_dung_elem = content_element.find_element(By.CSS_SELECTOR, 'div.x6s0dn4.x78zum5.xdt5ytf.x5yr21d.xl56j7k.x10l6tqk.x17qophe.x13vifvy.xh8yej3 div div')
                            noi_dung = noi_dung_elem.text
                            print("2")
                        except Exception as e:
                            noi_dung = ""
                    
                    if not noi_dung:
                        try:
                            noi_dung_elem = content_element.find_elements(By.CSS_SELECTOR, 'div.html-div.xdj266r.x11i5rnm.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1e56ztr span span')
                            noi_dung = " ".join([element.text for element in noi_dung_elem])
                            print("2.1")
                        except Exception as e:
                            noi_dung = ""

                    if not noi_dung:
                        try:
                            url_image_elem = content_element.find_element(By.CSS_SELECTOR, 'div.xqtp20y.x6ikm8r.x10wlt62.x1n2onr6 div img')
                            url_image = url_image_elem.get_attribute("src")
                            noi_dung = extract_text_from_image(url_image)
                            print("2.3")
                        except Exception as e:
                            noi_dung = ""

                    print(f"STT: {count+1}")
                    print(f"Tên nhóm: {ten_nhom}")
                    # print(f"URL nhóm: {row[0]}")
                    # print(f"URL bài viết: {url_bai_viet}")
                    # print(f"Số comment: {so_comment}")
                    # print(f"URL người dùng: {url_nguoi_dung}")
                    print(f"Tên người dùng: {ten_nguoi_dung}")
                    # print(f"URL cá nhân: {url_profile}")
                    print(f"Nội dung: {noi_dung}")
                    print(f"Thời gian: {thoi_gian}")
                    print("-"*40)

                    group_data = {
                        'Tên nhóm': ten_nhom,
                        'Nội dung': noi_dung,
                        'Tên người dùng': ten_nguoi_dung,
                        'URL cá nhân': url_profile,
                        'Số comment': so_comment,
                        'URL nhóm': row[0],
                        'URL bài viết': url_bai_viet,
                        'URL người dùng': url_nguoi_dung,
                        'Thời gian': thoi_gian,
                        'Ngày tháng năm': thoi_gian_text
                    }

                    if ten_nguoi_dung.lower() == "người tham gia ẩn danh" or ten_nguoi_dung == "":
                        print("Bỏ qua tên người dùng ẩn danh.")
                    else:
                        if not check_duplicate_content(noi_dung, spreadsheet_id, sheet_name):
                            # groups_data.append(group_data)
                            print("Đã thêm dữ liệu vào danh sách.")
                            save_to_gg_sheet([group_data], '1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI', 'ỨNG VIÊN PHÂN TÍCH')
                        else:
                            print("Dữ liệu đã tồn tại, bỏ qua.")
                except Exception as e:
                    print(f"Lỗi khi tìm phần tử trong đường dẫn {url_bai_viet}: {str(e)}")

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(2)
            except Exception as e:
                print(e)
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(2) 

            count += 1
            if flag:
                break
        if flag:
            break

    for group in groups_data:
        print(group)

    # if len(groups_data) > 0:
        # save_to_excel(groups_data)

driver.quit()
