import sys
import pandas as pd
import time
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from openaitool import analyzeAndSplitJobContent, analyzeJobInformation

import rapidjson
messages_data = []
i = 0
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def authenticate_google_sheets():
    credentials = Credentials.from_service_account_file(
        "hellojobv5-bbd1a88506df.json", scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    return service


def analyze_job():
    start_time = time.time()
    service = authenticate_google_sheets()
    RANGE_NAME = "KHO ĐƠN 13/5!D2:D"
    result = service.spreadsheets().values().get(
        spreadsheetId='1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI', range=RANGE_NAME
    ).execute()
    values = result.get('values', [])

    if not values:
        print("Không tìm thấy dữ liệu.")
        return
    global messages_data, i
    global lastSenderName
    unique_messages = []
    rowInserted = 1
    for chatItem in values:
        # groupName = chatItem[0]
        # lastSenderName = chatItem[1]
        message = chatItem[0]
        if message:
            if message and message not in unique_messages:
                unique_messages.append(message)
                analyzeJobContent = analyzeAndSplitJobContent(message)
                analyzeJobContentUsage = analyzeJobContent.usage
                choiceJsonStr = analyzeJobContent.choices[0].message.content
                count = 0
                try:
                    if not choiceJsonStr:
                        decodedJobs = [choiceJsonStr]
                    else:
                        decodedJobs = rapidjson.loads(choiceJsonStr)
                except Exception:
                    decodedJobs = [choiceJsonStr]
                    pass
                print(f"{decodedJobs}")
                for job in decodedJobs:
                    if len(job) >= 2:
                        # phân tích thông tin công việc
                        analyzeJobInfo = analyzeJobInformation(job)
                        # print(f"{analyzeJobInfo}")
                        prompt_tokens = 0
                        completion_tokens = 0
                        if count == 0:
                            prompt_tokens = analyzeJobContentUsage.prompt_tokens
                            completion_tokens = analyzeJobContentUsage.completion_tokens
                            count += 1
                        jobInforString = analyzeJobInfo.choices[0].message.content
                        analyzeJobInfoUsage = analyzeJobInfo.usage
                        prompt_tokens += analyzeJobInfoUsage.prompt_tokens
                        completion_tokens += analyzeJobInfoUsage.completion_tokens
                        prompt_price = round(prompt_tokens * 2.50 / 1000000, 4)
                        completion_price = round(completion_tokens * 10.00 / 1000000, 4)

                        # new_row = [job, ""]
                        new_row = [job]
                        
                        try:
                            jobInfor = rapidjson.loads(jobInforString)
                            print(f"{jobInfor}")
                            
                            # nếu là tin rác thì bỏ qua
                            # if jobInfor.get('postType', '').lower() == 'tin rác':
                            #     print("Bỏ qua tin rác")
                            #     continue
                                
                            formatedJob=formatJob(jobInfor)
                            print(f"{formatedJob}")
                            print(f"===========")
                            new_row += formatedJob[:4] + [""] + formatedJob[4:17] + [""] + formatedJob[17:]
                            new_row += [prompt_tokens, completion_tokens,
                                        prompt_price, completion_price]
                        except Exception as e:
                            print(e)
                            pass
                        new_row.insert(0, int(time.time()))
                        append_row_to_google_sheet(service, new_row)
                        rowInserted += 1
                    end_time = time.time()
                    print(f"Đã xử lý {rowInserted} dòng trong {end_time - start_time} giây.")
                if len(unique_messages) >= 200:
                    unique_messages.clear()
                    sys.exit()
    
def append_row_to_google_sheet(service, values):
    sheet = service.spreadsheets()
    body = {
        'values': [values]
    }
    result = sheet.values().append(
        spreadsheetId='1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI',
        range='KHO ĐƠN ĐÃ PHÂN TÍCH 13/5!A2',  
        valueInputOption='RAW',
        body=body
    ).execute()
    print(f"Đã ghi thành công: {result.get('updates').get('updatedCells')} ô.")


def formatJob(data):
    fields = [
        "postType",
        "visa",
        "languageLevel",
        "gender",
        "job",
        "specialConditions",
        "workLocation",
        "hourlyWage",
        "basicSalary",
        "realSalary",
        "success-candidate",
        "makeAI",
        "min_age",
        "max_age",
        "date",
        "phone",
        "phi",
        "back",
        "coche",
    ]

    result = []
    for field in fields:
        # Use .get() to avoid KeyError if the field is missing in the data object
        value = data.get(field, 'Empty')
        if value == '' or value == 'Empty' or value == 'Không cung cấp':
            value = ''
        elif isinstance(value, list):
            value = ';'.join(sorted(set(value)))
        result.append(value)
    return result


# get_contact()
# time.sleep(10)

if __name__ == "__main__":
    analyze_job()
