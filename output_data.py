# trich xuat du lieu tu database zalo_message.db
import sqlite3
import pandas as pd
import os
from datetime import datetime

def export_sqlite_to_excel(db_path, output_path):
    # Kết nối database
    conn = sqlite3.connect(db_path)

    # Truy vấn dữ liệu từ bảng zalo_messages dựa theo cột id
    query = """
    SELECT 
        id,
        group_name,
        poster,
        content,
        group_link,
        created_at,
        date,
        image_url
    FROM zalo_messages
    ORDER BY id ASC
    """
    
    df = pd.read_sql_query(query, conn)
    
    if os.path.exists(output_path):
        existing_df = pd.read_excel(output_path)
        # Kết hợp dữ liệu mới và cũ, loại bỏ trùng lặp
        combined_df = pd.concat([df, existing_df]).drop_duplicates()

    else:
        combined_df = df
    
    # Ghi dữ liệu ra Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        combined_df.to_excel(writer, sheet_name='zalo_messages', index=False)

    conn.close()
    print(f"✅ Đã xuất dữ liệu ra: {output_path}")

# --- Chạy chương trình ---
db_file = "zalo_messages.db"
output_folder = "F:/"  # <- đường dẫn cố định 
excel_filename = "dulieu_zalo.xlsx"
excel_output = os.path.join(output_folder, excel_filename)

export_sqlite_to_excel(db_file, excel_output)
