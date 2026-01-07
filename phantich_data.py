from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file('hellojobv5-8406e0a8eed7.json')
service = build('sheets', 'v4', credentials=creds)

def label_job_or_spam(spreadsheet_id, sheet_name):
    try:
        # Đọc dữ liệu cột B (nội dung)
        service = build('sheets', 'v4', credentials=creds)
        range_name = f'{sheet_name}!C2:C'
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        job_keywords = ['tìm đơn', 'xin đơn', 'ai có đơn', 'tim don', 'cần tìm', 'cần đơn']
        spam_keywords = ['lương', 'về tay', 'đơn hàng']

        labels = []
        for row in values:
            content = row[0].lower() if row else ""
            label = "Khác"
            if any(kw in content for kw in job_keywords):
                label = "ỨNG VIÊN"
            elif any(kw in content for kw in spam_keywords):
                label = "VIỆC LÀM NHẬT"
            else:
                label = "TIN RÁC"
            labels.append([label])

        # Ghi nhãn vào cột K (cột 11, bắt đầu từ K2)
        update_range = f'{sheet_name}!K2:K{len(labels)+1}'
        body = {'values': labels}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=update_range,
            valueInputOption='RAW',
            body=body
        ).execute()
        print("Đã cập nhật nhãn vào cột K.")
    except Exception as e:
        print(f"Lỗi khi gán nhãn: {str(e)}")

label_job_or_spam('1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI', 'ỨNG VIÊN PHÂN TÍCH')