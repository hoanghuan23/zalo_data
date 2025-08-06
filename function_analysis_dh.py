import time
from openaitool import analyzeAndSplitJobContent, analyzeJobInformation, analysisPostType
from analyze_job import formatJob
from zalo_fetcher import get_column_letter
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import rapidjson

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def authenticate_google_sheets():
    credentials = Credentials.from_service_account_file(
        "hellojobv5-8406e0a8eed7.json", scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    return service

def analyPostType():
    service = authenticate_google_sheets()
    spreadsheet_id = '1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI'
    sheet_name = 'ĐƠN HÀNG PHÂN TÍCH'
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
                print(f"Dòng {idx} đã được xử lý, bỏ qua.")
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

                print(f"Dòng {idx}: Đã ghi phân loại: {post_type_data['postType']}")

                if post_type_data['postType'] == 'VIỆC LÀM NHẬT':
                    analyze_and_update_sheet(spreadsheet_id, sheet_name, idx)

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
                print(job_data)
                formatted_job = formatJob(job_data)
                print(f"Đã phân tích {formatted_job}")

                update_values = []

                for field in formatted_job:
                    update_values.append(field if field is not None else "")

                update_values = update_values[:3] + [""] + update_values[3:] 

                start_col_index = ord('L') - 64
                last_col_index = start_col_index + len(update_values) - 1
                last_col = get_column_letter(last_col_index)
                update_ranger = f"{sheet_name}!L{row_index}:{last_col}{row_index}"
                body = {
                    'values': [update_values]
                }
                update_result = service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=update_ranger,
                    valueInputOption='RAW',
                    body=body
                ).execute()

                processed_status = f"{sheet_name}!AE{row_index}"
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

if __name__ == "__main__":
    analyPostType()