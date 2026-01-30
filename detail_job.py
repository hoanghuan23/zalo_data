from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json

def load_rules(path="rules.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def apply_rules(rawE, rawI, rules):
    rawE = rawE.lower().strip() if rawE else ""
    rawI = rawI.lower().strip() if rawI else ""

    for rule in rules:
        if any(k in rawE for k in rule["contains_e"]) and any(k in rawI for k in rule["contains_i"]):
            return rule["value"]
    return ""


def update_job_row_by_row(row_index):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file("hellojobv5-8406e0a8eed7.json", scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)

    spreadsheet_id = "1ccRbwgDPelMZmJlZSKtxbWweZ9UsgvgYjkpvMX1x1TI"
    sheet_name = "ĐƠN HÀNG PHÂN TÍCH"

    rules = load_rules()

    # --- Lấy tổng số dòng ---
    # metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    # sheet_info = next(s for s in metadata["sheets"] if s["properties"]["title"] == sheet_name)
    # last_row = sheet_info["properties"]["gridProperties"]["rowCount"]

    # --- Lặp từng dòng ---
    # for row in range(2, last_row + 1):

        # Đọc ô L và P của dòng
    range_L = f"{sheet_name}!L{row_index}"
    range_P = f"{sheet_name}!P{row_index}"

    rawE = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_L
    ).execute().get("values", [[""]])[0][0]

    rawI = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_P
    ).execute().get("values", [[""]])[0][0]

    # Áp rule
    value = apply_rules(rawE, rawI, rules)
    print(value)
    return value

        # Update vào cột O của dòng đó
        # update_range = f"{sheet_name}!O{row}"
        # service.spreadsheets().values().update(
        #     spreadsheetId=spreadsheet_id,
        #     range=update_range,
        #     valueInputOption="RAW",
        #     body={"values": [[value]]}
        # ).execute()
