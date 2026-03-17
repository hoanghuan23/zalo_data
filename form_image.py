# -*- coding: utf-8 -*-
import os
import requests
from PIL import Image
import io
import json
from openai import OpenAI
import base64
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JOB_POSTING_SCHEMA = {
    "type": "object",
    "properties": {
        "isValid": {
            "type": "boolean",
            "description": "True NẾU VÀ CHỈ NẾU hình ảnh là một đơn tuyển dụng lao động có cấu trúc dạng BẢNG rõ ràng. False trong mọi trường hợp khác.",
        },
        "details": {
            "type": "array",
            "description": "Một mảng các đối tượng, mỗi đối tượng đại diện cho một hàng thông tin trong đơn tuyển dụng. Chỉ trả về nếu isValid là true.",
            "items": {
                "type": "object",
                "properties": {
                    "hangMuc": {
                        "type": "string",
                        "description": "Tên của hạng mục (ví dụ: 'Địa điểm làm việc', 'Ngành nghề').",
                    },
                    "noiDung": {
                        "type": "string",
                        "description": "Nội dung chi tiết của hạng mục. Giữ nguyên định dạng gốc như in đậm, in nghiêng bằng cú pháp Markdown.",
                    },
                },
                "required": ["hangMuc", "noiDung"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["isValid", "details"],
    "additionalProperties": False,
}
    

def generate_job_posting_data(image_url):
    prompt = """ You are an expert recruitment director specializing in Japan labor export with 20 years of experience.

Your task is to analyze the uploaded image and extract job posting data from a TABLE only.

STEP 1 — IMAGE VALIDATION (CRITICAL & STRICT)
Determine whether the image is a REAL JOB POSTING TABLE.

Requirements:
- Must contain a visible table/grid layout with ≥ 2 columns and ≥ 3 rows.
- Text blocks / flyers / posters không chia hàng rõ ràng = NOT a table.

If the image is NOT a valid table → return ONLY:
{ "isValid": false }

STOP and do not proceed further.

STEP 2 — DATA EXTRACTION RULES (STRICT FORMAT KEEPING)
If valid table:

- Extract ALL rows into JSON based on the provided schema.
- DO NOT extract or infer STT from the image.
- Each row corresponds to exactly ONE object in "details".

FLATTENING RULE:
- If a cell contains sub-lists, bullet points, or multiple sections
  (e.g. "a. Text", "b. Text"),
  DO NOT create new JSON keys.
- Combine all content into ONE "noiDung" string.
- Use "\n" for line breaks.

FORMAT PRESERVATION:
- Preserve original data EXACTLY, including:
  • **bold**, *italic*, UPPERCASE
  • symbols, units, spacing
- Highlighted or emphasized salary/important fields = treat as **bold**.

STRICT RULES:
- You MUST NOT rewrite, paraphrase, summarize, or normalize meaning.
- You MUST NOT invent or infer any information not visible in the image.
- If content is unclear → return "" or "Không rõ".

10STEP 3 — JAPAN LOCATION AUTOCORRECT RULE
If a row represents workplace information (detect keywords):
[ "Địa điểm", "Địa điểm làm việc", "Địa chỉ", "Nơi làm việc",
  "Làm việc tại", "Location", "Workplace", "勤務先" ]

If the content contains a Japanese prefecture/city
AND spelling is clearly incorrect:

- Correct ONLY the prefecture/city name.
- Keep all other text and formatting unchanged.

Examples:
"Tokoy" → "Tokyo"
"Hokaido" → "Hokkaido"
"Gifu ken" → "Gifu"

If unsure → do NOT assume → keep original text.

OUTPUT REQUIREMENT (ABSOLUTE)
- Return ONLY valid JSON following the provided schema.
- NO explanation.
- NO markdown.
- NO text outside JSON.
- NO invisible characters.
- NO additional keys.

If valid table → return full object.
If invalid → return ONLY:
{ "isValid": false }"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}, 
                        }
                    ],
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "job_posting_schema",
                    "schema": JOB_POSTING_SCHEMA,
                },
            },
        )
        
        # usage = response.usage
        # print("=" * 10)
        # print("Function: Phân tích Markdown Array")
        # print("Input token", usage.prompt_tokens)
        # print("Output token", usage.completion_tokens)
        # print("Total token", usage.total_tokens)
        # print("=" * 10)

        raw = response.choices[0].message.content
        data = json.loads(raw)
        return data

    except Exception as e:
        print(f"Lỗi gọi OpenAI hoặc xử lý JSON: {e}")
        return None
