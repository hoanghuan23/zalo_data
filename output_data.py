# trich xuat du lieu tu database zalo_message.db
import sqlite3
import pandas as pd
import os

def export_sqlite_to_excel(db_path, output_path):
    # Kết nối database
    conn = sqlite3.connect(db_path)

    # Truy vấn dữ liệu từ bảng zalo_messages
    query = """
    SELECT 
        group_name,
        poster,
        content,
        group_link,
        created_at,
        date,
        image_url
    FROM zalo_messages
    ORDER BY created_at DESC
    """
    
    df = pd.read_sql_query(query, conn)
    
    # Ghi dữ liệu ra Excel
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='zalo_messages', index=False)

    conn.close()
    print(f"✅ Đã xuất dữ liệu ra: {output_path}")

# --- Chạy chương trình ---
db_file = "zalo_messages.db"
output_folder = "F:/"  # <- đường dẫn cố định 
excel_filename = os.path.splitext(os.path.basename(db_file))[0] + ".xlsx"
excel_output = os.path.join(output_folder, excel_filename)

export_sqlite_to_excel(db_file, excel_output)
