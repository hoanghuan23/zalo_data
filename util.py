import re


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


def formatGender(value):
    try:
        match value.lower():
            case "nam":
                return 'MALE'
            case "nữ":
                return "FEMALE"
            case 'cả nam và nữ':
                return "BOTH"
            case _:
                return None
    except Exception:
        return None


def formatTatoo(value):
    try:
        match value:
            case "có xăm nhỏ (kín)":
                return 'nhận xăm'
            case "có xăm to":
                return 'nhận xăm'
            case _:
                return None
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


def remove_non_digits(input_str):
    # Giữ lại các ký tự là số (0-9) và loại bỏ tất cả ký tự khác
    input_str = input_str.replace(',', '.')
    return re.sub(r'[^0-9\.]', '', input_str)


def formatJob(data):
    fields = [
        "contact", "country", "visa", "career", "workLocation",
        "interviewFormat", "language", "languageLevel", "fee",
        "back", "quantity", "basicSalary", "realSalary", "minAge",
        "maxAge", "gender", "interviewDay", "height", "weight",
        "dominantHand", "requiredQualifications", "numberRecruits",
        "haveTattoo", "vgb", "specialConditions"
    ]
    result = []
    for field in fields:
        # Use .get() to avoid KeyError if the field is missing in the data object
        value = data.get(field, 'Empty')
        if value == '' or value == 'Empty':
            value = 'Không rõ'
        result.append(value)
    return result


def formatRecruitment(data):
    fields = [
        "dateOfBirth",
        "hometown",
        "gender",
        "height",
        "weight",
        "country",
        "workLocation",
        "visa",
        "career",
        "language",
        "languageLevel",
        "requiredQualifications",
        "fee",
        "basicSalary",
        "realSalary",
        "haveTattoo",
        "vgb",
        "specialConditions"
    ]
    result = []
    for field in fields:
        # Use .get() to avoid KeyError if the field is missing in the data object
        value = data.get(field, 'Empty')
        if value == '' or value == 'Empty':
            value = 'Không rõ'
        result.append(value)
    return result

def columnIndex(column_letter):
    column_letter = column_letter.upper()  # Đảm bảo chữ hoa
    index = 0
    for char in column_letter:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1  # Trả về chỉ số 0-based

def formatVisa(input):
    try:
        match input:
            case "KS ĐẦU VIỆT":
                return 'Kỹ sư đầu Việt'
            case "Kỹ sư đầu Việt":
                return 'Kỹ sư đầu Việt'
            case "KS KO XÁC ĐỊNH TỪ ĐẦU NÀO":
                return "Kỹ sư"
            case "Kỹ sư không xác định từ đầu nào":
                return "Kỹ sư"
            case 'KS ĐẦU NHẬT':
                return "Kỹ sư đầu Nhật"
            case 'Kỹ sư đầu Nhật':
                return "Kỹ sư đầu Nhật"
            case 'TTS 3 NĂM':
                return "Thực tập sinh 3 năm"
            case 'Thực tập sinh 3 năm':
                return "Thực tập sinh 3 năm"
            case 'TTS 1 NĂM':
                return "Thực tập sinh 1 năm"
            case 'Thực tập sinh 1 năm':
                return "Thực tập sinh 1 năm"
            case 'TTS 3 GO':
                return "Thực tập sinh 3 go"
            case 'Thực tập sinh 3 Go':
                return "Thực tập sinh 3 go"
            case 'TKT ĐẦU NHẬT':
                return "Tokutei đầu Nhật"
            case 'Tokutei đầu Nhật':
                return "Tokutei đầu Nhật"
            case 'TKT ĐẦU VIỆT':
                return "Tokutei đầu Việt"
            case 'Tokutei đầu Việt':
                return "Tokutei đầu Việt"
            case 'TKT ĐI MỚI':
                return "Tokutei đi mới"
            case 'Tokutei đi mới':
                return "Tokutei đi mới"
            case 'TKT KO XÁC ĐỊNH TỪ ĐẦU NÀO':
                return "Tokutei"
            case 'Tokutei không xác định từ đầu nào':
                return "Tokutei"
            case _:
                return input
    except Exception:
        return None
def process_japan_regions(input_string):
    # Bước 1: Tách chuỗi thành mảng
    input_array = [item.strip() for item in input_string.replace(', ',',').split(",")]
    
    # Bước 2: Danh sách Tỉnh và Vùng
    regions = {
        "Hokkaido": ["Hokkaido"],
        "Tohoku": ["Aomori", "Iwate", "Miyagi", "Akita", "Yamagata", "Fukushima"],
        "Kanto": ["Ibaraki", "Tochigi", "Gunma", "Saitama", "Chiba", "Tokyo", "Kanagawa"],
        "Chubu": [
            "Niigata", "Toyama", "Ishikawa", "Fukui", "Yamanashi", 
            "Nagano", "Gifu", "Shizuoka", "Aichi"
        ],
        "Kinki (Kansai)": ["Mie", "Shiga", "Kyoto", "Osaka", "Hyogo", "Nara", "Wakayama"],
        "Chugoku": ["Tottori", "Shimane", "Okayama", "Hiroshima", "Yamaguchi"],
        "Shikoku": ["Tokushima", "Kagawa", "Ehime", "Kochi"],
        "Kyushu": ["Fukuoka", "Saga", "Nagasaki", "Kumamoto", "Oita", "Miyazaki", "Kagoshima"],
        "Okinawa": ["Okinawa"],
    }
    
    # Tạo danh sách các vùng và ánh xạ tỉnh sang vùng
    region_names = set(regions.keys())
    prefecture_to_region = {pref: region for region, prefs in regions.items() for pref in prefs}
    
    # Bước 3: Phân tích mảng, xác định Tỉnh và Vùng
    output = []
    added_regions = set()  # Để kiểm soát các vùng đã được thêm
    
    for item in input_array:
        # Nếu là Vùng
        if item in region_names:
            if item not in added_regions:
                output.append(item)
                added_regions.add(item)
        # Nếu là Tỉnh
        elif item in prefecture_to_region:
            region = prefecture_to_region[item]
            output.append(f"{item}, {region}")

    # Bước 4: Trả về kết quả
    return "; ".join(output)
languageLevels=['N5', 'N4', 'N3', 'N2', 'N1']
def get_lowest_language_level(input_string):
    # Danh sách các cấp độ ngoại ngữ theo thứ tự tăng dần
    
    # Tách chuỗi input thành danh sách
    components = input_string.replace(', ',',').split(',')
    
    # Lọc ra các cấp độ hợp lệ
    valid_levels = [level for level in components if level in languageLevels]
    
    # Trả về cấp độ thấp nhất nếu tìm thấy, ngược lại trả về None
    if valid_levels:
        return min(valid_levels, key=languageLevels.index)
    else:
        return None
    