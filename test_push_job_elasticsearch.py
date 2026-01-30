import re
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
from elasticsearch_tool_job_new import createCrawledJob, findLastID
from util import columnIndex
import random
import string

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI'


def authenticate_google_sheets():
    credentials = Credentials.from_service_account_file(
        "hellojobv5-8406e0a8eed7.json", scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    return service


def read_data_from_sheet():
    service = authenticate_google_sheets()
    RANGE_NAME = "ĐƠN HÀNG PHÂN TÍCH!A:AJ"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME
    ).execute()
    values = result.get('values', [])

    if not values:
        print("Không tìm thấy dữ liệu.")
        return

    # Dòng đầu tiên giả sử là header
    header = values[0]
    data_rows = values[1:]
  
    # Lấy dữ liệu từ các cột mong muốn trong một vòng lặp
    num_columns = len(header)
    filtered_data = []
    for row in data_rows:
        newRow = []
        
        # Lặp qua từng cột trong phạm vi số cột của header
        for i in range(num_columns):
            if i < len(row):  
                value = None if row[i].strip().lower() in ["không rõ", "empty", ""] else row[i].strip()
            else: 
                value = None  
            
            newRow.append(value)
        
        filtered_data.append(newRow)
    # lastID='DH59984'
    lastID = findLastID()
    print("Last ID: "+ lastID)
    nextID = int(lastID.replace('DH', ''))+1
    today = datetime.now()
    formatted_date = today.strftime('%d%m')
    sequential_values=[]
    startRow=None
    count = 2
    print("chạy tới đây")
    for row in filtered_data:
        # if row[0] or len(row[0]) > 0:
        if not row[0]:
            if startRow is None:
                startRow = count
            updatedIds = createCrawledJob(row, nextID, formatted_date)
            sequential_values.append([','.join(updatedIds)])
            nextID = nextID+len(updatedIds)
        count = count+1
    update_range = f"ĐƠN HÀNG PHÂN TÍCH!A{startRow}:A{count}"
    update_body = {
        'values': sequential_values
    }
    try:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=update_range,
            valueInputOption='USER_ENTERED',
            body=update_body
        ).execute()
    except Exception as e:
        print("Lỗi ggsheet: "+str(count)+'. '+e)

if __name__ == "__main__":
    read_data_from_sheet()
