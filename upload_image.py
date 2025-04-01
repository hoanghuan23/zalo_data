import boto3
import mimetypes
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import time
import random
import os


load_dotenv()       
bucket_name='cdn.hellojob.jp'
aws_access_key= os.getenv('AWS_ACCESS_KEY')
aws_secret_key= os.getenv('AWS_SECRET_KEY')
region_name='ap-southeast-1'


def upload_to_s3(file_path):
    content_type = mimetypes.guess_type(file_path)[0]
    # Khởi tạo client S3
    extension = file_path.split('.')[-1]
    print(extension)
    s3_key=f'upload/hellojobv5/job-crawled/images/{generate_random_image_name(extension)}'
    s3 = boto3.client('s3',
                      aws_access_key_id=aws_access_key,
                      aws_secret_access_key=aws_secret_key,
                      region_name=region_name)

    try:
        s3.upload_file(Filename=file_path, Bucket=bucket_name, Key=s3_key, ExtraArgs={'ACL': 'public-read', 'ContentDisposition': 'inline', 'ContentType': content_type})
        imageS3Url=f"https://cdn.hellojob.jp/{s3_key}"
        return imageS3Url
    except FileNotFoundError:
        print("❌ File không tồn tại.")
        return False
    except NoCredentialsError:
        print("❌ Thiếu thông tin xác thực AWS.")
        return False

def generate_random_image_name(extension):
    millis = int(time.time() * 1000)
    suffix = random.randint(100, 999)
    return f"{millis}{suffix}.{extension}"

# if __name__ == "__main__":
#     local_file_path = "F:/images/anhcanh.jpg"  # Thay đổi đường dẫn file local của bạn
#     result = upload_to_s3(local_file_path)
#     if result:
#         print("Link ảnh sau khi upload:")
#         print(result)