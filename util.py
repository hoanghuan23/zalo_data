# -*- coding: utf-8 -*-
import os
import google.generativeai as genai
import requests
from PIL import Image
import io
import json

# ==============================================================================
# HƯỚNG DẪN SỬ DỤNG
# ==============================================================================
#
# 1. CÀI ĐẶT CÁC THƯ VIỆN CẦN THIẾT:
#    pip install google-generativeai requests Pillow
#
# 2. THIẾT LẬP API KEY:
#    - Lấy API Key của bạn từ Google AI Studio.
#    - Cách 1 (Khuyến khích): Tạo một biến môi trường tên là 'GEMINI_API_KEY'
#      và gán giá trị API Key của bạn vào đó.
#      (Ví dụ: export GEMINI_API_KEY="your_api_key_here")
#    - Cách 2: Thay thế trực tiếp chuỗi "YOUR_GEMINI_API_KEY" trong code.
#
# 3. CHẠY THỬ NGHIỆM:
#    - Ở cuối file này, có một đoạn code ví dụ trong `if __name__ == "__main__":`.
#    - Thay thế `image_url` bằng link ảnh bạn muốn kiểm tra.
#    - Chạy file này từ terminal: python src/util.py
#
# ==============================================================================

# --- CẤU HÌNH ---


# --- CÁC HÀM XỬ LÝ ---

try:
    # Cấu hình API key từ biến môi trường
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        # Nếu không có biến môi trường, hãy thay thế key của bạn ở đây
        GEMINI_API_KEY = "AIzaSyBQ9lPPgDwFteApFyR1avTK7y75vb3KieI" 
        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
            print("CẢNH BÁO: Vui lòng cung cấp Gemini API Key.")

    genai.configure(api_key=GEMINI_API_KEY)
    
    # Khởi tạo model
    MODEL = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Lỗi khi khởi tạo Gemini: {e}")
    MODEL = None

def generate_html_string(posting_data):
    """
    Tạo một chuỗi HTML hoàn chỉnh từ dữ liệu đơn tuyển dụng.

    Args:
        posting_data (dict): Một dictionary chứa 'jobType' và 'details' (dạng Markdown).

    Returns:
        str: Một chuỗi HTML hoàn chỉnh, tự chứa với style inline.
    """
    job_type = posting_data.get('jobType', '')
    details_md = posting_data.get('details', '')

    note_row_html = """
    <tr>
        <td colspan="3" style="padding: 8px; border: 1px solid #e5e7eb; text-align: center; font-weight: bold; background-color: #F2B92A;">
            MỌI THÔNG TIN KHÔNG CÓ TRONG ĐƠN HÀNG SẼ HỎI KHI PHỎNG VẤN
        </td>
    </tr>
    """

    # Chuyển đổi bảng Markdown sang các hàng <tr> của HTML
    table_html = ''
    table_rows = details_md.strip().split('\n')
    # Bỏ 2 dòng đầu của Markdown table (header và dòng phân cách)
    for row in table_rows[2:]:
        cells = [cell.strip() for cell in row.split('|')[1:-1]]
        if len(cells) == 3:
            stt_style = 'padding: 8px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;'
            cell_style = 'padding: 8px; border: 1px solid #e5e7eb;'
            table_html += f'<tr><td style="{stt_style}">{cells[0]}</td><td style="{cell_style}">{cells[1]}</td><td style="{cell_style}">{cells[2]}</td></tr>\n'

    # Ghép các phần lại thành HTML hoàn chỉnh
    full_html = f'''
      <!DOCTYPE html>
      <html lang="vi">
      <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Thông Báo Đơn Hàng: {job_type}</title>
          <style>
              body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 0; padding: 2rem; background-color: #f9fafb; color: #111827; }}
              .container {{ max-width: 794px; margin: auto; background-color: white; padding: 2rem; border: 1px solid #e5e7eb; border-radius: 0.5rem; }}
              h1, h2 {{ text-align: center; }}
              h1 {{ font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem; }}
              h2 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; }}
              table {{ width: 100%; border-collapse: collapse; font-size: 0.875rem; }}
              th, td {{ padding: 8px; border: 1px solid #e5e7eb; text-align: left; }}
              th {{ background-color: #19A6DF; color: white; text-align: center; }}
          </style>
      </head>
      <body>
          <div class="container">
              <h1>THÔNG BÁO ĐƠN HÀNG</h1>
              <h2>{job_type}</h2>
              <table>
                  <thead>
                      <tr>
                          <th>STT</th>
                          <th>Hạng mục</th>
                          <th>Nội dung</th>
                      </tr>
                  </thead>
                  <tbody>
                      {table_html}
                      {note_row_html}
                  </tbody>
              </table>
          </div>
      </body>
      </html>
    '''
    return full_html.strip()

def generate_job_posting_data(image_url):
    """
    Hàm chính: nhận link ảnh, gọi AI để lấy markdown, và tạo ra HTML.

    Args:
        image_url (str): Link URL công khai của ảnh cần xử lý.

    Returns:
        dict: Một dictionary chứa 'markdown' và 'formImageHTML', hoặc {'error': '...'} nếu có lỗi.
    """
    if not MODEL:
        return {"error": "Mô hình Gemini chưa được khởi tạo. Vui lòng kiểm tra API Key."}

    try:
        # Tải ảnh từ URL
        response = requests.get(image_url)
        response.raise_for_status()  # Ném lỗi nếu request không thành công
        image = Image.open(io.BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        return {"error": f"Không thể tải ảnh từ URL: {e}"}
    except Exception as e:
        return {"error": f"Lỗi khi xử lý ảnh: {e}"}

    # Nội dung prompt, sao chép từ file TypeScript
    prompt = '''
        You are an expert director of a labor export company with 20 years of experience in the Japanese market. You understand these job forms perfectly. Analyze the job posting image.
        Your task is to perform two steps:
        1.  **Classify the Job Type**: Based on the content, determine which of the following categories the job falls into: "Thực tập sinh 3 năm", "Thực tập sinh 1 năm", "Thực tập sinh 3 Go", "Thực tập sinh", "Tokutei đầu Nhật", "Tokutei đầu Việt", "Tokutei đi mới", "Kỹ sư, tri thức đầu Nhật", "Kỹ sư, tri thức đầu Việt". If the image only mentions "Thực tập sinh" generically without a duration, use the "Thực tập sinh" category. Set this value for the 'jobType' field.
        2.  **Extract and Restructure Details**: Identify all key-value pairs (e.g., "Địa điểm" and "Aichi"). You MUST restructure ALL extracted information into a single Markdown table with exactly three columns: "STT", "Hạng mục", and "Nội dung". Automatically generate sequential numbers for the "STT" column.

            For example:
            | STT | Hạng mục             | Nội dung                                 |
            |-----|----------------------|------------------------------------------|
            | 1   | Địa điểm làm việc    | Aichi                                    |
            | 2   | Ngành nghề           | Chế biến thực phẩm                       |
            | ... | ...                  | ...                                      |
      
        **Formatting Rule**: While extracting content for the "Nội dung" column, you MUST preserve the original text formatting. This includes **bold text**, *italic text*, and words in ALL CAPS. Represent bold and italics using standard Markdown syntax.

        Return the final table as a single Markdown string in VIETNAMESE for the 'details' field.

        **CRITICAL**: You MUST IGNORE and OMIT any partner company information (logo, name, contact details). The 'details' field should NOT include the main title of the job posting as that is already handled by the 'jobType' field.
        The output must be a valid JSON object.
    '''
    
    # Yêu cầu AI trả về kết quả dưới dạng JSON
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json")

    try:
        # Gửi yêu cầu đến AI
        response = MODEL.generate_content(
            [prompt, image],
            generation_config=generation_config
        )
        
        # Parse kết quả JSON
        markdown_data = json.loads(response.text)
        
        # Tạo chuỗi HTML
        html_output = generate_html_string(markdown_data)
        
        # Trả về kết quả cuối cùng
        # return {
        #     "markdown": markdown_data,
        #     "formImageHTML": html_output
        # }
        return markdown_data

    except Exception as e:
        return {"error": f"Lỗi trong quá trình gọi AI hoặc xử lý kết quả: {e}"}

# ==============================================================================
# KHỐI MÃ CHẠY THỬ NGHIỆM
# ==============================================================================
if __name__ == "__main__":
    # --- THAY LINK ẢNH CỦA BẠN VÀO ĐÂY ---
    # Ví dụ: một ảnh đơn hàng bất kỳ
    test_image_url = "https://cdn.hellojob.jp/upload/hellojobv5/job-crawled/images/1764642583558792.jpg" 

    print(f"Đang xử lý ảnh từ URL: {test_image_url}")

    # Gọi hàm chính
    result = generate_job_posting_data(test_image_url)

    if "error" in result:
        print(f"\nĐÃ XẢY RA LỖI:\n{result['error']}")
    else:
        print("\n--- XỬ LÝ THÀNH CÔNG! ---\n")

        # In ra một phần để kiểm tra
        print("1. DỮ LIỆU MARKDOWN (JSON):")
        # print(json.dumps(result['markdown'], indent=2, ensure_ascii=False))
        
        print("\n" + "="*50 + "\n")
        print(result)

        # print("2. KẾT QUẢ HTML (có thể lưu lại và mở bằng trình duyệt):")
        # print(result['formImageHTML'])

        # Gợi ý: Lưu file HTML để xem
        with open("output.text", "w", encoding="utf-8") as f:
            f.write(result)
        print("\nĐã lưu kết quả vào file 'output.html'. Bạn có thể mở file này bằng trình duyệt.")
