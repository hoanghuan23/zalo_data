from playwright.sync_api import sync_playwright
import boto3
from botocore.exceptions import ClientError
import re
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from upload_image import generate_random_image_name

load_dotenv()       
bucket_name='cdn.hellojob.jp'
aws_access_key= os.getenv('AWS_ACCESS_KEY')
aws_secret_key= os.getenv('AWS_SECRET_KEY')
region_name='ap-southeast-1'


def html_to_screenshot_and_url(html_string: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # Test với headless=True để giống production
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ],
        )
        context = browser.new_context(
            viewport={"width": 794, "height": 500},
            device_scale_factor=1.5,
        )
        page = context.new_page()

        page.set_content(html_string, wait_until="domcontentloaded")

        # Nếu cần chờ thêm render (tùy trường hợp có JS nặng)
        # page.wait_for_timeout(2000)

        screenshot_bytes = page.screenshot(
            type="jpeg",
            quality=100,
            full_page=True,
        )

        if not screenshot_bytes:
            print("Không chụp được ảnh screenshot")
            return ""

        # === LƯU TẠM LOCAL ĐỂ TEST ===
        # local_path = "test_screenshot_headless.jpg"
        # with open(local_path, "wb") as f:
        #     f.write(screenshot_bytes)

        # abs_path = os.path.abspath(local_path)
        # print(f"Ảnh tạm lưu tại: {abs_path}")
        # print(f"Kích thước: {len(screenshot_bytes) / (1024 * 1024):.2f} MB")

        # try:
        #     os.startfile(local_path)  # Mở ảnh tự động (Windows)
        # except:
        #     print("Mở thủ công file:", abs_path)

        # === UPLOAD LÊN S3 ===
        s3_client = boto3.client('s3',
                        aws_access_key_id=aws_access_key,
                        aws_secret_access_key=aws_secret_key,
                        region_name=region_name)

        try:
            s3_key=f"upload/hellojobv5/job-crawled/form-image-hj/{generate_random_image_name('jpg')}"
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=screenshot_bytes,
                ContentType="image/jpeg",
            )
            print(f"Upload thành công lên S3: s3://{bucket_name}/{s3_key}")

            # Tạo public URL (nếu bucket public)
            url = f"https://cdn.hellojob.jp/{s3_key}"

            # Nếu bucket KHÔNG public, dùng signed URL (hết hạn sau 1 giờ)
            # url = s3_client.generate_presigned_url(
            #     'get_object',
            #     Params={'Bucket': s3_bucket, 'Key': s3_key},
            #     ExpiresIn=3600  # 1 giờ
            # )

            print(f"URL ảnh: {url}")

        except ClientError as e:
            print(f"Lỗi upload S3: {e}")
            url = ""

        return url

        # return url  # nếu cần


def generate_html_from_markdown(
    visa_detail: str, details: Optional[List[Dict[str, str]]]
) -> str:
    if not details or not visa_detail:
        return ""

    visa = visa_detail.replace("Tokutei", "Đặc định") if visa_detail else None

    stt_style = "padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;"
    cell_style = "padding: 8px 6px; border: 1px solid #e5e7eb;"

    table_html = ""

    for item in details:
        stt = item.get("stt", "")
        hang_muc = item.get("hangMuc", "")
        noi_dung = item.get("noiDung", "")

        # Convert markdown (**bold**, *italic*) to HTML
        desc = noi_dung
        desc = re.sub(r"(\*\*|__)(.*?)\1", r"<b>\2</b>", desc)
        desc = re.sub(r"\*(.*?)\*", r"<i>\1</i>", desc)

        table_html += f"""
        <tr>
            <td style="{stt_style}">{stt}</td>
            <td style="{cell_style}">{hang_muc}</td>
            <td style="{cell_style}">{desc}</td>
        </tr>
        """

    full_html = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thông Báo Đơn Hàng: {visa}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&family=Noto+Sans+JP:wght@100..900&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Montserrat','Noto Sans JP','Arial',sans-serif;
            margin: 0; padding: 0; color: #111827;
        }}
        .container {{
            width: 100%;
            max-width: 794px;
            margin: auto;
            background-color: white;
            padding: 1rem 0 0;
            box-sizing: border-box;
        }}
        h1, h2 {{ text-align: center; color: #111827; }}
        h1 {{ font-size: 1.5rem; font-weight: bold; margin: 0; }}
        h2 {{ font-size: 1.25rem; font-weight: 600; margin: 0 0 1rem; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12pt;
            line-height: 1.3rem;
        }}
        th, td {{
            padding: 8px;
            border: 1px solid #e5e7eb;
            text-align: left;
            word-break: break-word;
            color: #111827;
        }}
        th {{
            background-color: #19A6DF;
            color: white;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1></h1>
        <h2>{visa}</h2>
        <table>
            <thead>
                <tr>
                    <th style="width:25px">STT</th>
                    <th style="width:100px">Hạng mục</th>
                    <th>Nội dung</th>
                </tr>
            </thead>
            <tbody>
                {table_html}
                <tr>
                    <td colspan="3" style="background-color:#F2B92A; text-align:center; font-weight:bold;">
                        MỌI THÔNG TIN KHÔNG CÓ TRONG ĐƠN HÀNG SẼ HỎI KHI PHỎNG VẤN
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>
"""

    return full_html


# # Ví dụ chạy
# html = """
# <html lang="vi"><head>
#           <meta charset="UTF-8">
#           <meta name="viewport" content="width=device-width, initial-scale=1.0">
#           <title>Thông Báo Đơn Hàng: Đặc định đầu Nhật</title>
#           <link rel="preconnect" href="https://fonts.googleapis.com">
#           <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
#           <link href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&amp;family=Noto+Sans+JP:wght@100..900&amp;display=swap" rel="stylesheet">
#           <style>
#               body { font-family: 'Montserrat','Noto Sans JP', 'Arial', sans-serif; margin: 0; padding: 0; color: #111827; }
#               .container { width: 100%; max-width: 794px; margin: auto; background-color: white; padding: 1rem 0 0; box-sizing: border-box; }
#               h1, h2 { text-align: center; color: #111827; }
#               h1 { font-size: 1.5rem; font-weight: bold; margin-bottom: 0;margin-top:0 }
#               h2 { font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; margin-top:0 }
#               table { width: 100%; border-collapse: collapse; font-size: 12pt;line-height:1.3rem }
#               th, td { padding: 8px; border: 1px solid #e5e7eb; text-align: left; word-break: break-word; color: #111827; }
#               th { background-color: #19A6DF; color: white; text-align: center; }
#           </style>
#       </head>
#       <body>
#           <div class="container">
#               <h1></h1>
#               <h2>Đặc định đầu Nhật</h2>
#               <table>
#                   <thead>
#                       <tr>
#                           <th style="width:25px">STT</th>
#                           <th style="width:100px">Hạng mục</th>
#                           <th>Nội dung</th>
#                       </tr>
#                   </thead>
#                   <tbody>
#                       <tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">1</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Tên Công ty</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">THÔNG BÁO SAU KHI PHỎNG VẤN</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">2</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Địa điểm làm việc</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">TỈNH YAMAGATA (東置賜郡高畠町)</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">3</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Ngành nghề xin visa</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">TKT LẬP R LAP LINH KIỆN ĐIỆN TỬ
# 1/ Lắp ráp thiết bị điện - điện tử.
# 2/ Quản lí đội nhóm.</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">4</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Điều kiện tuyển dụng</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Số nhân viên cần tuyển:
# Nam: 1
# Số nhân viên nữ còn: 2
# Tuổi: Dưới 33 tuổi
# Thị lực: Tốt
# Thuận tay: Phải,Trái
# Giới tính: Nam
# Tình trạng hôn nhân: Không yêu cầu</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">5</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Yêu cầu chung</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Trình độ học vấn: Không yêu cầu
# Trình độ tiếng Nhật: N3 (hoặc tương đương N3)
# 1. Ứng viên hoàn thành chương trình TTS ngành lắp ráp linh kiện điện tử 電気電子機器.
# 2. Ứng viên có năng lực quản lí đội nhóm 1 &gt; 4 năm.
# Yêu cầu khác:
# 1. Ứng viên có năng lực quản lí đội nhóm.
# 2. Tính thần trách nhiệm cao.</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">6</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Lương cơ bản</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">1. <b>LƯƠNG GIỚI CAO</b>: <b>1.212 Yên/h</b> (Tăng ca * 1.25 = <b>1.515 Yên/h</b>).
# 2. TĂNG CA ỔN ĐỊNH (khoảng 30h/tháng).
# 3. LƯƠNG VỀ TAY CAO khoảng &gt; 19 Man/tháng.</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">7</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Bảo hiểm, thuế</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Theo quy định của pháp luật Nhật Bản.</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">8</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Tiền nhà, điện nước</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">1/ TIỀN NHÀ <b>20.000 YEN/THÁNG</b>.
# 2/ Dưới cả 1 người/phòng.
# 3/ Điện nước ga trị theo mức thực tế.</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">9</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Ngày nghỉ</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Theo quy định của công ty.</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">10</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Thời gian làm việc</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">8:00 - 17:00
# giai lao 60 phút</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">11</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Dự kiến thi tuyển</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Tháng 1</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">12</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Hình thức thi tuyển</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Phỏng vấn online 2 lần</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">13</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Dự kiến xuất cảnh</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Tháng 4</td>
#     </tr><tr>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb; text-align: center; background-color: #AFC536;">14</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Lưu ý</td>
#       <td style="padding: 8px 6px; border: 1px solid #e5e7eb;">Công ty đã có thực tập sinh và muốn tìm viên có năng lực quản lý làm Leader.</td>
#     </tr>
#                       <tr>
#                         <td colspan="3" style="background-color: #F2B92A; text-align: center; font-weight: bold;">MỌI THÔNG TIN KHÔNG CÓ TRONG ĐƠN HÀNG SẼ HỎI KHI PHỎNG VẤN</td>
#                       </tr>
#                   </tbody>
#               </table>
#           </div>
      
      
#     </body></html>
# """

# html_to_screenshot_and_url(html, "cdn.hellojob.jp", "temp/playwright/test.jpg")
