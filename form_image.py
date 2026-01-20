import os
import requests
from PIL import Image
import io
import json
from openai import OpenAI
import fitz  # PyMuPDF
import base64


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Schema JSON như cũ
JOB_POSTING_SCHEMA = {
    "type": "object",
    "properties": {
        "isValid": {"type": "boolean",
                    "description": "True NẾU VÀ CHỈ NẾU hình ảnh là một đơn tuyển dụng lao động có cấu trúc dạng BẢNG rõ ràng. False trong mọi trường hợp khác."
                },
        "details": {
            "type": "array",
            "description": "Một mảng các đối tượng, mỗi đối tượng đại diện cho một hàng thông tin trong đơn tuyển dụng. Chỉ trả về nếu isValid là true.",
            "items": {
                "type": "object",
                "properties": {
                    "stt": {"type": "string", "description": "Số thứ tự của hàng trong bảng."},
                    "hangMuc": {"type": "string", "description": "Tên của hạng mục (ví dụ: 'Địa điểm làm việc', 'Ngành nghề')."},
                    "noiDung": {"type": "string", "description": "Nội dung chi tiết của hạng mục. Giữ nguyên định dạng gốc như in đậm, in nghiêng bằng cú pháp Markdown."}
                },
                "required": ["stt", "hangMuc", "noiDung"]
            }
        }
    },
    "required": ["isValid"]
}

def generate_job_posting_data(image_url):
    try:
        img_bytes = requests.get(image_url).content
        image_base64 = Image.open(io.BytesIO(img_bytes))
    except Exception as e:
        print(f"Lỗi tải ảnh: {e}")
        return None

    prompt = ''' You are an expert recruitment director specializing in Japan labor export with 20 years of experience. Your task is to analyze the uploaded image and extract job posting data from a TABLE only.

    =====================================================
    STEP 1 — IMAGE VALIDATION (CRITICAL & STRICT)
    =====================================================
    Determine whether the image is a REAL JOB POSTING TABLE.
    Requirements:
    - Must contain a visible table/grid layout with ≥ 2 columns and ≥ 3 rows.
    - Text blocks/flyers/posters không chia hàng rõ ràng = NOT a table.
    - If the image is NOT a valid table → return ONLY:
    { "isValid": false }
    STOP and do not proceed further.

    =====================================================
    STEP 2 — DATA EXTRACTION RULES (STRICT FORMAT KEEPING)
    =====================================================
    If valid table:
    - Extract all rows into JSON based on provided schema.
    - Preserve original data EXACTLY including:
    • **bold**, *italic*, UPPERCASE
    • formatting symbols, line breaks, units, spacing
    - Highlighted/emphasized salary or fields = treat as **bold**
    - You MUST NOT rewrite, paraphrase, summarize, or normalize meaning.
    - You MUST NOT invent information not visible in the image.
    If unclear → return "" or "Không rõ".

    =====================================================
    STEP 3 — JAPAN LOCATION AUTOCORRECT RULE
    =====================================================
    If a row represents workplace information (detect keywords):
    [ "Địa điểm", "Địa điểm làm việc", "Địa chỉ", "Nơi làm việc", "Làm việc tại", "Location", "Workplace", "勤務先" ]
    → If content contains a Japanese prefecture/city and spelling appears incorrect,
    Correct ONLY prefecture/city spelling to the nearest valid name.
    Examples:
    "Tokoy" → "Tokyo", "Hokaido" → "Hokkaido", "Gifu ken" → "Gifu"
    Keep all other text + formatting unchanged.
    If unsure → do not assume → return original.

    =====================================================
    OUTPUT REQUIREMENT (IMPORTANT)
    =====================================================
    Return ONLY a valid JSON following schema below.
    No explanation, no extra texts, no markdown block formatting.
    If valid table → return full object.
    If invalid → return only { "isValid": false }.
    '''

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",     # hoặc "gpt-4.1" nếu muốn mạnh hơn
            messages=[
                {"role": "user", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "job_posting_schema",
                    "schema": JOB_POSTING_SCHEMA
                }
            }
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)
        return data

    except Exception as e:
        print(f"Lỗi gọi OpenAI hoặc xử lý JSON: {e}")
        return None


if __name__ == "__main__":
    test_image_url = "https://cdn.hellojob.jp/upload/hellojobv5/job-crawled/images/1765161461959291.pdf"
    result = generate_job_posting_data(test_image_url)
    with open("job_posting_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)