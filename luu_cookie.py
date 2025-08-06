from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import time

driver = webdriver.Chrome()
url = "https://www.facebook.com/"
driver.get(url)
time.sleep(60)

try:
    cookies = driver.get_cookies()
    pickle.dump(cookies, open("facebook_cookies_02.pkl", "wb"))
    print("Cookie đã được lưu.")

finally:
    driver.quit()
