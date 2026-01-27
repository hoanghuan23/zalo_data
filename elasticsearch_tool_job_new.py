import time
import re
import sys
import os
from opensearchpy import OpenSearch
import json
import random
import string
from datetime import datetime
from form_image import generate_job_posting_data

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from util import columnIndex, formatVisa, process_japan_regions, get_lowest_language_level, formatGender
# from openaitool import generateEmbedding
DOMAIN = 'https://sync.hellojob.jp'
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
es = OpenSearch(
    hosts=[DOMAIN],
    # Thêm xác thực username và password
    http_auth=(USERNAME, PASSWORD)
)
template = "{gender}; country: {country}; visa: {visa}; career: {career}; workLocation: {workLocation}; language: {language}; qualifications: {requiredQualifications}, haveTattoo: {haveTattoo}, vgb: {vgb}, specialConditions: {specialConditions}"


with open('JOBS.json', 'r', encoding='utf-8') as f:
    JOBS = json.load(f)

def check_expired(visa: str, created_date: int, interview_date: str = None, industry: str = None) -> int:
    """
    Trả về ngày hết hạn (timestamp dạng milliseconds) dựa trên logic:
    - Nếu có ngày phỏng vấn: hết hạn là ngày phỏng vấn, nhưng không quá 60 ngày kể từ ngày đăng.
    - Nếu không có ngày phỏng vấn: tính theo loại visa và ngành.
    """

    DAY = 24 * 60 * 60 * 1000  # milliseconds trong 1 ngày

    # Nếu có ngày phỏng vấn
    if interview_date:
        try:
            interview_dt = datetime.strptime(interview_date, "%d-%m-%Y")
            interview_time = int(interview_dt.timestamp() * 1000)
            diff_days = (interview_time - created_date) / DAY
            if diff_days <= 60:
                return interview_time
            else:
                return created_date + 60 * DAY
        except ValueError:
            # Nếu format ngày sai, coi như không có ngày phỏng vấn
            pass

    # Nếu không có ngày phỏng vấn
    special_industries = ["Thực phẩm", "Điện, điện tử", "Cơ khí, chế tạo máy"]
    expire_days = 14

    if visa in ["Thực tập sinh 3 năm", "Thực tập sinh 1 năm"]:
        expire_days = 14
    elif visa == "Thực tập sinh 3 Go":
        expire_days = 10
    elif visa in ["Đặc định đầu Việt", "Đặc định đầu Nhật"]:
        expire_days = 3 if (industry in special_industries) else 10
    elif visa in ["Đặc định đi mới", "Kỹ sư, tri thức đầu Việt"]:
        expire_days = 14
    elif visa == "Kỹ sư, tri thức đầu Nhật":
        expire_days = 10

    return created_date + expire_days * DAY
     
def generate_jp_code():
    prefix = "JP-"
    random_letters = ''.join(random.choices(string.ascii_uppercase, k=5))
    now = datetime.now()
    month = f"{now.month:02d}"    
    year_suffix = str(now.year)[-1]
    return f"{prefix}{random_letters}{month}{year_suffix}"




def createCrawledJob(json, newID, flagDate):
    # try:
    createdDate = int(time.time() * 1000)
    # id = json[columnIndex('A')]
    groupName = json[columnIndex('B')]
    sender = json[columnIndex('C')]
    baseContent = json[columnIndex('D')]
    country = 'Nhật Bản'
    visa = json[columnIndex('L')]
    visas = []
    if visa:
        visa = visa.replace(', ', ',')
        visas = visa.split(',')
    career = None
    job = json[columnIndex('O')]
    filter = {}
    if job and len(job) > 0:
        job = job.replace('"', '')
        pattern = r'(TTS#|TKT#|KS#)(.*?)(?=(?:TTS#|TKT#|KS#|$))'
        matches = re.findall(pattern, job, flags=re.DOTALL)
        jobs = []
        for prefix, content in matches:
            # Ghép prefix với phần nội dung, có thể strip() nếu muốn bỏ khoảng trắng thừa
            content = content.strip()
            if content.endswith(','):
                content = content[:-1].rstrip()
            jobs.append(prefix + content)
                
        print(f"{job}")
        print(f"{jobs}")
        job=jobs[0]
        splits = job.split('#')
        visaPrefix = splits[0]
        job = splits[1]
        visaCodePrefix = None
        if visaPrefix == 'TTS':
            visaCodePrefix = '1.1'
        elif visaPrefix == 'TKT':
            visaCodePrefix = '1.2'
        elif visaPrefix == 'KS':
            visaCodePrefix = '1.3'
        result = next(
            (item for item in JOBS if item["value"].startswith(
                visaCodePrefix) and item["label"] == job),
            None
        )
        if result:
            career = result['parent']
            filter['job'] = result
    # else:
        # print('#')
        # return 1
    workLocation = json[columnIndex('R')]
    if workLocation:
        workLocation = process_japan_regions(workLocation)
    language = None
    languageLevel = json[columnIndex('M')]
    if languageLevel == 'KHÔNG TIẾNG':
        languageLevel = None
    if languageLevel:
        languageLevel = get_lowest_language_level(languageLevel)
        if not languageLevel:
            languageLevel = json[columnIndex('M')]
        language = 'Nhật Bản'
    basicSalaryHour = None
    basicSalaryHourCode = None
    try:
        basicSalaryHour = json[columnIndex('S')].replace(
            ',', '.').replace('.00', '')
        if basicSalaryHour:
            basicSalaryHour = float(basicSalaryHour)
            basicSalaryHourCode = 'y/h'
    except Exception as ex:
        # print(ex)
        pass
    basicSalary = None
    basicSalaryCode = None
    try:
        basicSalary = json[columnIndex('T')]
        if basicSalary:
            basicSalaryCode = 'JPY'
    except Exception as ex:
        # print(ex)
        pass
    realSalary = None
    realSalaryCode = None
    try:
        realSalary = json[columnIndex('U')]
        if realSalary:
            realSalaryCode = 'JPY'
    except Exception as ex:
        # print(ex)
        pass
    gender = json[columnIndex('N')]
    specialConditions = json[columnIndex('Q')]
    groupLink = json[columnIndex('E')]
    source = json[columnIndex('AF')]
    postedTime = int(time.time())
    if json[columnIndex('F')]:
        postedTime = int(json[columnIndex('F')])
    aiContent = json[columnIndex('W')]
    minAge = json[columnIndex('X')]
    if minAge is not None and len(minAge) > 0:
        minAge = int(minAge)
    maxAge = json[columnIndex('Y')]
    if maxAge is not None and len(maxAge) > 0:
        maxAge = int(maxAge)
    numberRecruits = json[columnIndex('V')]
    if numberRecruits is not None and len(numberRecruits) > 0:
        numberRecruits = int(numberRecruits)
    interviewDay = json[columnIndex('Z')]
    # if interviewDay:
    #     interviewDay = interviewDay+'/2025'
    formImage = json[columnIndex('H')]
    
    if formImage:
        markdown_details = generate_job_posting_data(formImage)
        if markdown_details and markdown_details.get('isValid'):
            markdown_details = markdown_details.get('details')
        else:
            markdown_details = None
    else:
        markdown_details = None

    if not markdown_details:
        return ['INVALID']

    fee = formatNumberValue(json[columnIndex('AB')], None)
    back = formatNumberValue(json[columnIndex('AC')], None)
    quantity = formatNumberValue(json[columnIndex('AD')], None)
    # salerID = json[columnIndex('AW')]
    code = generate_jp_code()
    phoneNumber = json[columnIndex('AA')]
    avatar=None
    try:
        avatar=get_job_image(job, career)
    except Exception as e:
        pass
    expiredDate = check_expired(visa=visa, created_date=createdDate, interview_date=interviewDay, industry=career)
    matchingContent = f"""Giới tính: {gender}; Nước: {country}; Visa: {visa}; Ngành: {career}; Nghề: {job}; Địa điểm: {workLocation}; Ngôn ngữ: {
        language}; Lương: từ {basicSalary or realSalary} {basicSalaryCode or realSalaryCode}; Điều kiện đặc biệt: {specialConditions}"""
    document = {
        "groupName": groupName,
        "sender": sender,
        "baseContent": baseContent,
        "aiContent": aiContent,
        "country": country,
        "visa": visa,
        "career": career,
        "job": job,
        "workLocation": workLocation,
        "language": language,
        "languageLevel": languageLevel,
        "fee": fee,
        "back": back,
        "quantity": quantity,
        "basicSalaryHour": basicSalaryHour,
        "basicSalaryHourCode": basicSalaryHourCode,
        "basicSalary": basicSalary,
        "basicSalaryCode": basicSalaryCode,
        "realSalary": realSalary,
        "realSalaryCode": realSalaryCode,
        "minAge": minAge,
        "maxAge": maxAge,
        "gender": formatGender(gender),
        "interviewDay": interviewDay,
        "numberRecruits": numberRecruits,
        "specialConditions": specialConditions,
        "matchingContent": matchingContent,
        "source": source,
        "groupLink": groupLink,
        "flagDate": flagDate,
        "time": postedTime,
        "postedDate": postedTime,
        "filter": filter,
        "createdDate": createdDate,
        "formImage": formImage,
        "code": code,
        # "salerID": salerID,
        # "createdID": salerID,
        "avatar": avatar,
        "phoneNumber": phoneNumber,
        "contacts": {
            "phoneVN": phoneNumber
        },
        "expiredDate": expiredDate,
        "formMarkdownArray": markdown_details
    }
    # print(document)
    ids = []
    if not markdown_details:
        return None
    for visaItem in visas:  
        id = f'DH{newID}'
        # id = json[columnIndex('A')]
        ids.append(id)
        visa = formatVisa(visaItem)
        document['id'] = id
        document['visa'] = visa
        print(visa)
        response = es.index(index='hellojobv5-job-crawled',
                            id=id, body=document)
        newID += 1
    # print(visa,career,job)
    print(','.join(ids))
    return ids

def findLastID():
    try:
        search_body = {
            "size": 1,
            "sort": [
                {
                    "id.keyword": {
                        "order": "desc"
                    }
                }
            ]
        }
        response = es.search(index='hellojobv5-job-crawled', body=search_body)
        if len(response['hits']['hits']):
            maxIdDoc = response['hits']['hits'][0]
            return maxIdDoc['_id']
        else:
            return None
    except Exception as e:
        print(f"Error retrieving last ID: {e}")
        return None


def formatSpecialConditions(value):
    try:
        return value.replace(', ', ',').split(',')
    except Exception:
        return None


def escapeEmpty(value):
    try:
        return value.replace(', Empty', '').replace('Empty,', '').replace('Empty', '')
    except Exception:
        return None


def formatDominantHand(value):
    try:
        match value:
            case "tay phải":
                return 'RIGHT'
            case "tay trái":
                return "LEFT"
            case 'cả hai tay':
                return "BOTH"
            case _:
                return None
    except Exception:
        return None


def formatNumberValue(value, defaultValue):
    try:
        return float(remove_non_digits(value))
    except Exception:
        return defaultValue

with open('mapping_images.json', 'r', encoding='utf-8') as f:
    mapping_images = json.load(f)

def get_job_image(job: str, career: str) -> str:
    mapping_image = next((item for item in mapping_images if job in item["newJobs"]), None)

    if not mapping_image:
        mapping_image = next((item for item in mapping_images if career in item["newJobs"]), None)

    if not mapping_image:
        return "/img/sample/no-image.jpg"

    images = mapping_image["images"]

    # Nếu chỉ có 1 ảnh thì trả về luôn
    if len(images) == 1:
        return images[0]

    return random.choice(images)


def remove_non_digits(input_str):
    # Giữ lại các ký tự là số (0-9) và loại bỏ tất cả ký tự khác
    input_str = input_str.replace(',', '.')
    return re.sub(r'[^0-9\.]', '', input_str)
