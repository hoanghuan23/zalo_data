import base64
import os

client = os.getenv("OPENAI_API_KEY")

# Hàm chuyển ảnh thành base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Hàm gửi ảnh vào OpenAI để trích xuất văn bản
def extract_text_from_image(image_path):
    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-4.1-nano-2025-04-14",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Đọc toàn bộ nội dung văn bản chỉ có trong hình ảnh này bằng tiếng Việt, không thêm bất kỳ câu văn AI nào, không thêm tiêu đề, không thêm ký tự |. Chỉ trả lại đúng phần văn bản gốc của ảnh dưới dạng đoạn văn."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]   
            }
        ],
    )
    result = response.choices[0].message.content.strip()
    print("Response:", result)
    if result.lower() == "không có văn bản":
        result = ''
    return result

# Chạy chương trình
if __name__ == "__main__":
    image_path = "C:/Users/ACER/Downloads/donh.jpg"
    extracted_text = extract_text_from_image(image_path)
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(extracted_text)
    print("Extracted Text:", extracted_text)
