# Zalo Dashboard Crawler & Job Pipeline

Hệ thống thu thập bài đăng tuyển dụng từ Zalo, phân tích bằng OpenAI, chuẩn hóa dữ liệu lên Google Sheets và đẩy dữ liệu sang OpenSearch cho hệ thống tìm kiếm.

## 1) Mục tiêu dự án

- Thu thập nội dung tuyển dụng từ các nhóm Zalo.
- Trích xuất nội dung từ ảnh (OCR bằng mô hình vision).
- Phân loại bài viết (`VIỆC LÀM NHẬT`, `ỨNG VIÊN`, `TIN RÁC`).
- Chuẩn hóa dữ liệu đơn hàng theo schema JSON.
- Đồng bộ dữ liệu sang Google Sheets, SQLite và OpenSearch.

## 2) Kiến trúc xử lý tổng quan

1. Selenium mở Zalo Web và duyệt các nhóm.
2. Đọc tin nhắn mới + ảnh đính kèm.
3. Upload ảnh lên S3 và OCR nội dung ảnh.
4. Ghi bản ghi thô vào SQLite + Google Sheets.
5. Gọi OpenAI để:
	 - phân loại loại bài,
	 - chuẩn hóa nội dung,
	 - phân tích trường dữ liệu công việc theo schema.
6. Bổ sung dữ liệu, dựng form ảnh (Playwright), cập nhật Google Sheets.
7. Push dữ liệu chuẩn hóa sang OpenSearch.

## 3) Cấu trúc file chính

- `zalo_fetcher.py`: tiến trình crawler chính (Selenium + xử lý ảnh + gọi pipeline phân tích).
- `openaitool.py`: các hàm gọi OpenAI để chuẩn hóa và phân tích nội dung.
- `function_analysis_dh.py`: phân loại/ghi dữ liệu phân tích theo dòng Google Sheet.
- `analyze_job.py`: phân tích nội dung job từ Google Sheet.
- `detail_job.py`: mapping rule cho cột job.
- `test_push_job_elasticsearch.py`: đọc dữ liệu sheet và tạo document push OpenSearch.
- `elasticsearch_tool_job_new.py`: logic tạo document và thao tác với OpenSearch.
- `upload_image.py`: upload/xóa ảnh trên S3.
- `playwright_util.py`: render HTML -> screenshot -> upload S3.
- `form_image.py`: phân tích ảnh đơn hàng để sinh dữ liệu chi tiết.
- `util.py`, `stringutils.py`: hàm tiện ích.
- `rules.json`, `JOBS.json`, `mapping_images.json`: dữ liệu cấu hình/mapping.

## 4) Yêu cầu hệ thống

- Python 3.10+ (khuyến nghị 3.11).
- Google Chrome.
- ChromeDriver tương thích phiên bản Chrome.
- Kết nối internet ổn định (OpenAI, Google Sheets API, AWS S3/OpenSearch).

## 5) Cài đặt nhanh

```bash
python -m venv .venv
```

### Windows

```powershell
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Cài dependencies:

```bash
pip install -U pip
pip install openai python-dotenv google-api-python-client google-auth boto3 botocore playwright selenium pillow imagehash requests opensearch-py python-rapidjson pandas
playwright install chromium
```

## 6) Cấu hình môi trường

Tạo file `.env` ở thư mục gốc:

```env
OPENAI_API_KEY=your_openai_api_key
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
```

### Google Service Account
Bạn cần:

1. Tạo service account trên Google Cloud.
2. Bật Google Sheets API.
3. Tải file JSON key và đặt đúng tên/path hoặc sửa lại path trong code.
4. Chia sẻ Google Sheet cho email service account với quyền chỉnh sửa.

## 7) Cách chạy

### Chạy crawler end-to-end (khuyến nghị)

```bash
python zalo_fetcher.py
```

Script này sẽ:

- mở Zalo Web,
- quét nhóm và lấy tin nhắn,
- xử lý ảnh + AI,
- ghi dữ liệu vào Sheets/SQLite,
- trigger các bước phân tích và push dữ liệu.

### Chạy từng bước riêng lẻ

1. Phân tích job từ sheet:

```bash
python analyze_job.py
```

2. Phân loại + cập nhật dữ liệu phân tích:

```bash
python function_analysis_dh.py
```

3. Đẩy dữ liệu từ sheet sang OpenSearch:

```bash
python test_push_job_elasticsearch.py
```

4. Update thủ công một bản ghi UV:

```bash
python update_uv.py
```

## 8) Dữ liệu đầu ra

- SQLite local: tự tạo file `zalo_messages.db` để lưu bản ghi crawl.
- Google Sheets: ghi vào các sheet cấu hình sẵn trong code.
- OpenSearch: tạo/cập nhật document đơn hàng cho hệ thống downstream.

