# Placeholder for Zalo crawling logic
import os
import pandas as pd
import pytesseract
import base64
import requests
import json
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime
import re
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)



browser = webdriver.Chrome()
browser.get('https://chat.zalo.me')
time.sleep(30)

unique_messages = set()
processed_images = set()

keywords = {
    "phân loại tin" : {
        "VIỆC LÀM NHẬT" : ["nhật", "japan", "jpn", "jp", "đầu n", "đầu v", "đầu việt nam", "đầu vn", "đầu việt", 
        "Hokkaido", "Hokkaido", "Tohaku", "Aomori", "Iwate", "Miyagi", "Akita", "Yamagata", "Fukushima", "Kanto", "Ibaraki", "Tochigi",
        "Gunma", "Saitama", "Chiba", "Tokyo", "Kanagawa", "Chūbu", "Niigata", "Toyama", "Ishikawa", "Fukui",
        "Yamanashi", "Nagano", "Gifu", "Shizuoka", "Aichi", "Kansal", "Mie", "Shiga", "Kyoto", "Osaka",
        "Hyogo", "Nara", "Wakayama", "Chūgoku", "Tottori", "Shimane", "Okayama", "Hiroshima", "Yamaguchi",
        "Shikoku", "Tokushima", "Kagawa", "Ehime", "Kochi", "Kyūshū", "Okinawa", "Fukuoka", "Saga",
        "Nagasaki", "Kumamoto", "Õita", "Miyazaki", "Kagoshima", "Okinawa"],
        "VIỆC LÀM NỘI ĐỊA" : ["BHXH", "BHYT", "làm việc tại KCN", "Bắc Giang", "Hải Phòng", "Hà Nội", "Bình Dương", "HCM"],
        "TIN RÁC" : ["tham gia nhóm đăng đơn tìm đơn free, cung cấp phần mềm", "phần mềm gửi tin nhắn", "nhóm không khóa, đăng free"],
        "ĐÀi LOAN" : ["đài loan", "đài bắc", "Đài trung", "trung"],
        "NƯỚC KHÁC" : ["HUNGARY", "PHÁP", "NGA"],
    },

    "Loại hình visa" : {
        # "Thực tập sinh 3 năm" : [ "tr/F", "tr/f", "10 tr / f", "10 Tr 1F", "5TRIỆU/F", "15tr/", "triệu/form", "tr/form", "mua form", "mua 20tr", "1tr/f", "5tr/f", "10trf", "20tr/f", "5600-1200-5tr/F", "5300 1500 cc 10", "5800-1400-10", "5300 1500 cc 10", "5800 1500 cc 15", "5800 1500 cc 10", "5800-1400-10tr", "PHÍ 5700 MG 1500 CC 10TR", "Tiến cử", "bao đỗ", "bao đậu", "gửi form", "Chỉ định đỗ", "xăm", "nhận xăm kín", "xăm nhỏ", "xăm lớn", "xăm to", "nhận xăm", "NHẬN XĂM HỞ" ],
        # "Thực tập sinh 1 năm" : ["1 năm"],
        # "Tokutei đầu Việt" : ["tokutei việt", "tokutei v", "tokutei việt nam", "tokutei vn", "tkt đ / việt", "đặc định"],
        # "KS ĐẦU VIỆT" : ["ks việt", "ks v", "ks việt nam", "ks vn", "ks đ/việt"],
        # "DU HỌC" : ["du học", "du học nhật", "du học nhật bản", "du học sinh"],
        # "2 Đầu" : ["việt - nhât", "nhật - việt", "2 đầu", "2 đầu việt nhật", "2 đầu nhật việt"], 
        "Thực tập sinh 3 năm" : [""],
    },

    "Giới tính" : {
        "nam" : ["nam"],
        "nữ" : ["nữ"],
        "Cả nam và nữ" : ["nam nữ", "nam/nữ"],
    },

    "Trình độ ngoại ngữ" : {
        "N1" : ["n1"],
        "N2" : ["n2"],
        "N3" : ["n3"],
        "N4" : ["n4"],
        "N5" : ["n5", "tiếng cơ bản"],
        "Kaiwa" : ["kaiwa"],
        "Không tiếng" : ["không tiếng", "không yêu cầu tiếng", "không yc tiếng"],
    },

    "Công việc chi tiết" : {
        "TTS#Nuôi sò điệp" : ["Nuôi sò điệp"],
        "TTS#Đánh cá lưới sào": ["Đánh cá lưới sào"], "TTS#Đặt lưới đánh cá": ["Đặt lưới đánh cá"],"TTS#Đánh cá lưới rê": ["Đánh cá lưới rê"], "TTS#Đánh cá lưới kéo": ["Đánh cá lưới kéo"],"TTS#Đánh cá lưới thả": ["Đánh cá lưới thả"],"TTS#Câu tôm, cua bằng lồng": ["Câu tôm, cua bằng lồng"],"TTS#Câu mực": ["Câu mực"],"TTS#Câu cá ngừ cần và dây": ["Câu cá ngừ cần và dây"],"TTS#Đánh cá dây câu dài": ["Đánh cá dây câu dài"],"TTS#Chăn nuôi bò": ["Chăn nuôi bò"],"TTS#Chăn nuôi bò sữa": ["Chăn nuôi bò sữa"],"TTS#Nhặt trứng gà": ["Nhặt trứng gà"],
        "TTS#Chăn nuôi gà": ["Chăn nuôi gà"],"TTS#Chăn nuôi lợn": ["Chăn nuôi lợn"],"TTS#Trồng nấm công nghệ cao": ["Trồng nấm công nghệ cao"],"TTS#Trồng nấm": ["Trồng nấm"],"TTS#Thu hoạch hoa": ["Thu hoạch hoa"],"TTS#Thu hoạch hoa quả": ["Thu hoạch hoa quả"],"TTS#Thu hoạch dâu tây": ["Thu hoạch dâu tây"],"TTS#Thu hoạch bắp cải": ["Thu hoạch bắp cải"],"TTS#Thu hoạch rau củ": ["Thu hoạch rau củ"],"TTS#Thu hoạch cà chua": ["Thu hoạch cà chua"],"TTS#Trồng rau củ": ["Trồng rau củ"],"TTS#Trồng cây ăn quả": ["Trồng cây ăn quả"],"TTS#Trồng trọt nhà kính": ["Trồng trọt nhà kính"],"TTS#Nấu bếp": ["Nấu bếp"],"TTS#Phụ bếp": ["Phụ bếp"],"TTS#Rửa bát": ["Rửa bát"],"TTS#Mua hàng": ["Mua hàng"],"TTS#Quản lý": ["Quản lý"],"TTS#Thu ngân": ["Thu ngân"],"TTS#Chạy bàn": ["Chạy bàn"],"TTS#Nhà hàng": ["Nhà hàng"],"TTS#Bếp viện": ["Bếp viện"],"TTS#Thức ăn cơ sở y tế": ["Thức ăn cơ sở y tế"],"TTS#Giăm bông, xúc xích...": ["Giăm bông, xúc xích..."],"TTS#Chế biến thịt bò, lợn": ["Chế biến thịt bò, lợn"],"TTS#Chế biến gia cầm": ["Chế biến gia cầm"],"TTS#Thịt lợn": ["Thịt lợn"],"TTS#Thịt bò": ["Thịt bò"],
        "TTS#Thịt gà": ["Thịt gà"],"TTS#Thái cá sashimi": ["Thái cá sashimi"],"TTS#Chế biến cá": ["Chế biến cá"],"TTS#Chế biến thuỷ sản sống": ["Chế biến thuỷ sản sống"],"TTS#Thuỷ sản gia công chế biến": ["Thuỷ sản gia công chế biến"],"TTS#Thuỷ sản khô": ["Thuỷ sản khô"],"TTS#Thuỷ sản sấy khô": ["Thuỷ sản sấy khô"],"TTS#Thuỷ sản ủ muối": ["Thuỷ sản ủ muối"],"TTS#Thuỷ sản xông khói": ["Thuỷ sản xông khói"],"TTS#Thuỷ sản lên men": ["Thuỷ sản lên men"],"TTS#Chiết xuất thuỷ sản": ["Chiết xuất thuỷ sản"],"TTS#Tẩm ướp thuỷ sản": ["Tẩm ướp thuỷ sản"],"TTS#Sản xuất mắm cá": ["Sản xuất mắm cá"],"TTS#Đóng hộp thực phẩm": ["Đóng hộp thực phẩm"],
        "TTS#Gia công đồ ăn liền": ["Gia công đồ ăn liền"],"TTS#Chế biến đồ ăn sẵn": ["Chế biến đồ ăn sẵn"],"TTS#Chế biến sushi": ["Chế biến sushi"],"TTS#Cửa hàng siêu thị": ["Cửa hàng siêu thị"],"TTS#Siêu thị": ["Siêu thị"],"TTS#Đồ konbini": ["Đồ konbini"],"TTS#Salad": ["Salad"],"TTS#Sản xuất dưa muối": ["Sản xuất dưa muối"],"TTS#Đồ ăn kèm": ["Đồ ăn kèm"],"TTS#Mỳ tôm": ["Mỳ tôm"],"TTS#Sản xuất mỳ": ["Sản xuất mỳ"],"TTS#Cơm hộp": ["Cơm hộp"],
        "TTS#Cơm nắm": ["Cơm nắm"],"TTS#Há cảo": ["Há cảo"],"TTS#Đậu hũ": ["Đậu hũ"],"TTS#Thực phẩm": ["Thực phẩm"],"TTS#Thực phẩm trứng": ["Thực phẩm trứng"],"TTS#Thực phẩm sữa": ["Thực phẩm sữa"],
        "TTS#Sản xuất bánh mì": ["Sản xuất bánh mì"],"TTS#Bánh gạo": ["Bánh gạo"],"TTS#Bánh ngọt": ["Bánh ngọt"],"TTS#Làm bánh kẹo": ["Làm bánh kẹo"],"TTS#Bánh kẹo": ["Bánh kẹo"],"TTS#Đóng gói bánh kẹo": ["Đóng gói bánh kẹo"],"TTS#Đóng gói rau": ["Đóng gói rau"],"TTS#Đóng gói rau củ": ["Đóng gói rau củ"],"TTS#Đóng gói rong biển": ["Đóng gói rong biển"],"TTS#Đóng gói cafe": ["Đóng gói cafe"],"TTS#Đóng gói mỹ phẩm": ["Đóng gói mỹ phẩm"],
        "TTS#Đóng gói công nghiệp": ["Đóng gói công nghiệp"],"TTS#Đóng gói": ["Đóng gói"],"TTS#Đóng sách": ["Đóng sách"],"TTS#In vỏ bánh kẹo": ["In vỏ bánh kẹo"],"TTS#In ống đồng": ["In ống đồng"],"TTS#In offset": ["In offset"],"TTS#Sản xuất hộp in": ["Sản xuất hộp in"],"TTS#Đục lỗ hộp in": ["Đục lỗ hộp in"],"TTS#Sản xuất hộp bìa cứng": ["Sản xuất hộp bìa cứng"],"TTS#Sản xuất hộp nhãn dán": ["Sản xuất hộp nhãn dán"],"TTS#Sản xuất vải lanh": ["Sản xuất vải lanh"],"TTS#Sản xuất pin năng lượng": ["Sản xuất pin năng lượng"],"TTS#Sản xuất linh kiện": ["Sản xuất linh kiện"],"TTS#Công việc cưa gỗ": ["Công việc cưa gỗ"],
        "TTS#Gỗ ép": ["Gỗ ép"],
        "TTS#Gia công sản phẩm gỗ": ["Gia công sản phẩm gỗ"],
        "TTS#Gia công đồ gia dụng": ["Gia công đồ gia dụng"],
        "TTS#Sửa chữa tủ điện": ["Sửa chữa tủ điện"],
        "TTS#Sửa chữa dụng cụ": ["Sửa chữa dụng cụ"],
        "TTS#Thiết kế bảng mạch in": ["Thiết kế bảng mạch in"],
        "TTS#Sản xuất bảng mạch in": ["Sản xuất bảng mạch in"],
        "TTS#Bản mạch in": ["Bản mạch in"],
        "TTS#Lắp ráp linh kiện bán dẫn": ["Lắp ráp linh kiện bán dẫn"],
        "TTS#Lắp ráp thiết bị điện tử": ["Lắp ráp thiết bị điện tử"],
        "TTS#Lắp ráp điện tử": ["Lắp ráp điện tử"],
        "TTS#Điện tử": ["Điện tử"],
        "TTS#Điện": ["Điện"],
        "TTS#Lắp tủ điện, tủ điều khiển": ["Lắp tủ điện, tủ điều khiển"],
        "TTS#Lắp thiết bị đóng, mở": ["Lắp thiết bị đóng, mở"],
        "TTS#Lắp ráp thiết bị điện khí": ["Lắp ráp thiết bị điện khí"],
        "TTS#Lắp ráp máy biến áp": ["Lắp ráp máy biến áp"],
        "TTS#Lắp ráp thiết bị điện quay": ["Lắp ráp thiết bị điện quay"],
        "TTS#Cuộn dây máy điện quay": ["Cuộn dây máy điện quay"],
        "TTS#Lắp ráp điện": ["Lắp ráp điện"],
        "TTS#Thi công điện": ["Thi công điện"],
        "TTS#Xử lý nhiệt tổng thể": ["Xử lý nhiệt tổng thể"],
        "TTS#Xử lý nhiệt một phần": ["Xử lý nhiệt một phần"],
        "TTS#Xử lý nhiệt bề mặt": ["Xử lý nhiệt bề mặt"],
        "TTS#Chế tạo máy": ["Chế tạo máy"],
        "TTS#Lắp đặt tủ lạnh": ["Lắp đặt tủ lạnh"],
        "TTS#Lắp đặt điều hoà": ["Lắp đặt điều hoà"],
        "TTS#Lắp đặt máy móc": ["Lắp đặt máy móc"],
        "TTS#Lắp ráp máy móc": ["Lắp ráp máy móc"],
        "TTS#Kiểm tra máy móc": ["Kiểm tra máy móc"],
        "TTS#Bảo trì máy móc": ["Bảo trì máy móc"],
        "TTS#Sử dụng máy tiện thường": ["Sử dụng máy tiện thường"],
        "TTS#Sử dụng máy tiện số": ["Sử dụng máy tiện số"],
        "TTS#Sử dụng máy phay": ["Sử dụng máy phay"],
        "TTS#Máy sản xuất tấm kim loại": ["Máy sản xuất tấm kim loại"],
        "TTS#Ép dập kim loại": ["Ép dập kim loại"],
        "TTS#Thi công kết cấu thép": ["Thi công kết cấu thép"],
        "TTS#Vận hành máy": ["Vận hành máy"],
        "TTS#Vận hành máy gia công": ["Vận hành máy gia công"],
        "TTS#Vận hành máy CNC": ["Vận hành máy CNC"],
        "TTS#Vận hành máy ép": ["Vận hành máy ép"],
        "TTS#Vận hành máy ép nhựa": ["Vận hành máy ép nhựa"],
        "TTS#Cơ khí": ["Cơ khí"],
        "TTS#Gia công cơ khí": ["Gia công cơ khí"],
        "TTS#Gia công tinh": ["Gia công tinh"],
        "TTS#Gia công kim loại - Tekko": ["Gia công kim loại - Tekko"],
        "TTS#Đúc": ["Đúc"],
        "TTS#Đúc gang": ["Đúc gang"],
        "TTS#Đúc kim loại màu": ["Đúc kim loại màu"],
        "TTS#Đúc khuôn": ["Đúc khuôn"],
        "TTS#Đúc khuôn buồng nóng": ["Đúc khuôn buồng nóng"],
        "TTS#Đúc khuôn buồng lạnh": ["Đúc khuôn buồng lạnh"],
        "TTS#Dập khuôn kim loại": ["Dập khuôn kim loại"],
        "TTS#Gia công ép đùn": ["Gia công ép đùn"],
        "TTS#Rèn": ["Rèn"],
        "TTS#Rèn bằng búa": ["Rèn bằng búa"],
        "TTS#Hoàn thiện dụng cụ nung chảy": ["Hoàn thiện dụng cụ nung chảy"],
        "TTS#Hoàn thiện khuôn": ["Hoàn thiện khuôn"],
        "TTS#Hoàn thiện sản phẩm ép đùn": ["Hoàn thiện sản phẩm ép đùn"],
        "TTS#Mạ điện": ["Mạ điện"],
        "TTS#Mạ kẽm nhúng nóng": ["Mạ kẽm nhúng nóng"],
        "TTS#Xử lý điện hóa nhôm": ["Xử lý điện hóa nhôm"],"TTS#Chế tạo kim loại tấm": ["Chế tạo kim loại tấm"],"TTS#Hàn": ["Hàn"],"TTS#Hàn thủ công": ["Hàn thủ công"],"TTS#Hàn xì": ["Hàn xì"],"TTS#Hàn khí": ["Hàn khí"],"TTS#Hàn bán tự động": ["Hàn bán tự động"],
        "TTS#Hàn kết cấu": ["Hàn kết cấu"],
        "TTS#Hàn khung thép": ["Hàn khung thép"],
        "TTS#Hàn tủ điện": ["Hàn tủ điện"],
        "TTS#Hàn tàu": ["Hàn tàu"],
        "TTS#Đóng tàu": ["Đóng tàu"],
        "TTS#Sơn": ["Sơn"],
        "TTS#Sơn phun": ["Sơn phun"],
        "TTS#Sơn kim loại": ["Sơn kim loại"],
        "TTS#Sơn cầu thép": ["Sơn cầu thép"],
        "TTS#Sơn công trình xây dựng": ["Sơn công trình xây dựng"],
        "TTS#Lắp ráp linh kiện ô tô": ["Lắp ráp linh kiện ô tô"],
        "TTS#Linh kiện ô tô": ["Linh kiện ô tô"],
        "TTS#Kiểm tra linh kiện ô tô": ["Kiểm tra linh kiện ô tô"],
        "TTS#Bảo dưỡng ô tô": ["Bảo dưỡng ô tô"],
        "TTS#Sửa chữa ô tô": ["Sửa chữa ô tô"],
        "TTS#Đúc nhựa": ["Đúc nhựa"],
        "TTS#Đúc nhựa nén": ["Đúc nhựa nén"],"TTS#Đúc nhựa thổi phồng": ["Đúc nhựa thổi phồng"],"TTS#Đúc nhựa thổi định hình": ["Đúc nhựa thổi định hình"],"TTS#Đúc nhựa cán xếp chồng": ["Đúc nhựa cán xếp chồng"],"TTS#Đục nhựa ép phun": ["Đục nhựa ép phun"],"TTS#Kiểm tra sản phẩm nhựa": ["Kiểm tra sản phẩm nhựa"],"TTS#Đúc khuôn cao su": ["Đúc khuôn cao su"],"TTS#Trộn và cán cao su": ["Trộn và cán cao su"],"TTS#Gia công ép đùn cao su": ["Gia công ép đùn cao su"],
        "TTS#Vật liệu composite nhiều lớp": ["Vật liệu composite nhiều lớp"],
        "TTS#In gốm": ["In gốm"],
        "TTS#Đúc gốm bằng áp lực": ["Đúc gốm bằng áp lực"],
        "TTS#Nặn gốm bằng bánh xoay": ["Nặn gốm bằng bánh xoay"],
        "TTS#Nhiên liệu rắn từ rác": ["Nhiên liệu rắn từ rác"],
        "TTS#Hàng hóa hàng không": ["Hàng hóa hàng không"],
        "TTS#Hỗ trợ mặt đất máy bay": ["Hỗ trợ mặt đất máy bay"],
        "TTS#Dọn dẹp khoang hành khách": ["Dọn dẹp khoang hành khách"],
        "TTS#Thiết bị khí nén đường sắt": ["Thiết bị khí nén đường sắt"],
        "TTS#Bảo trì đường sắt": ["Bảo trì đường sắt"],
        "TTS#Lái máy xây dựng": ["Lái máy xây dựng"],
        "TTS#Lái máy xúc": ["Lái máy xúc"],
        "TTS#Lái máy xúc lật": ["Lái máy xúc lật"],
        "TTS#Lái máy ủi": ["Lái máy ủi"],
        "TTS#Lái xe lu": ["Lái xe lu"],
        "TTS#Phá dỡ": ["Phá dỡ"],
        "TTS#San lấp mặt bằng": ["San lấp mặt bằng"],
        "TTS#Hút nước ngầm công trình": ["Hút nước ngầm công trình"],
        "TTS#Làm nền, móng": ["Làm nền, móng"],
        "TTS#Thi công móng thép": ["Thi công móng thép"],
        "TTS#Đổ nhựa đường": ["Đổ nhựa đường"],
        "TTS#Dựng giàn giáo": ["Dựng giàn giáo"],
        "TTS#Gia công sắt trong xưởng": ["Gia công sắt trong xưởng"],
        "TTS#Gia công khung thép trong xưởng": ["Gia công khung thép trong xưởng"],
        "TTS#Gia công khung thép": ["Gia công khung thép"],
        "TTS#Hàn khung thép trên cao": ["Hàn khung thép trên cao"],
        "TTS#Lắp ghép cốt thép": ["Lắp ghép cốt thép"],
        "TTS#Buộc thép": ["Buộc thép"],
        "TTS#Cốp pha công trình": ["Cốp pha công trình"],
        "TTS#Mộc cốp pha": ["Mộc cốp pha"],
        "TTS#Bê tông": ["Bê tông"],
        "TTS#Sản xuất bê tông": ["Sản xuất bê tông"],
        "TTS#Đổ bê tông áp lực": ["Đổ bê tông áp lực"],
        "TTS#Trát vữa": ["Trát vữa"],
        "TTS#Xây dựng tổng hợp": ["Xây dựng tổng hợp"],
        "TTS#Gia công vật liệu đá": ["Gia công vật liệu đá"],
        "TTS#Lát đá": ["Lát đá"],
        "TTS#Ốp lát gạch": ["Ốp lát gạch"],
        "TTS#Lợp mái nhà": ["Lợp mái nhà"],
        "TTS#Lợp ngói": ["Lợp ngói"],
        "TTS#Chống thấm": ["Chống thấm"],
        "TTS#Chống thấm trần nhà": ["Chống thấm trần nhà"],
        "TTS#Công trình chống nóng, lạnh": ["Công trình chống nóng, lạnh"],
        "TTS#Thợ mộc xây dựng": ["Thợ mộc xây dựng"],
        "TTS#Hoàn thiện sàn nhựa": ["Hoàn thiện sàn nhựa"],
        "TTS#Hoàn thiện sàn thảm": ["Hoàn thiện sàn thảm"],
        "TTS#Hoàn thiện ván": ["Hoàn thiện ván"],
        "TTS#Dán tường": ["Dán tường"],
        "TTS#Thi công dán tường": ["Thi công dán tường"],
        "TTS#Sơn xây dựng": ["Sơn xây dựng"],
        "TTS#Nội thất gỗ-xây dựng": ["Nội thất gỗ-xây dựng"],
        "TTS#Hoàn thiện nội thất": ["Hoàn thiện nội thất"], "TTS#Thi công lắp rèm": ["Thi công lắp rèm"],"TTS#Gia công đường ống": ["Gia công đường ống"],
        "TTS#Đường ống": ["Đường ống"],
        "TTS#Đường ống nước": ["Đường ống nước"],
        "TTS#Đường ống xây dựng": ["Đường ống xây dựng"],
        "TTS#Lắp đặt đường ống": ["Lắp đặt đường ống"],
        "TTS#Đường ống điều hoà": ["Đường ống điều hoà"],
        "TTS#Lắp điện lạnh, điều hòa": ["Lắp điện lạnh, điều hòa"],
        "TTS#Đường ống nhà máy": ["Đường ống nhà máy"],
        "TTS#Khoan giếng máy dập": ["Khoan giếng máy dập"],
        "TTS#Khoan giếng máy khoan": ["Khoan giếng máy khoan"],
        "TTS#Lắp đặt pin năng lượng": ["Lắp đặt pin năng lượng"],
        "TTS#Lắp đặt lò nung-xây dựng": ["Lắp đặt lò nung-xây dựng"],
        "TTS#Khung chắn toà nhà": ["Khung chắn toà nhà"],
        "TTS#Tấm kim loại ống gió": ["Tấm kim loại ống gió"],
        "TTS#Tấm kim loại kiến trúc": ["Tấm kim loại kiến trúc"],
        "TTS#Vệ sinh toà nhà": ["Vệ sinh toà nhà"],
        "TTS#Buồng phòng khách sạn": ["Buồng phòng khách sạn"],
        "TTS#(Khách sạn) Tiếp khách, quản lý vệ sinh": ["(Khách sạn) Tiếp khách, quản lý vệ sinh"],
        "TTS#Lễ tân khách sạn": ["Lễ tân khách sạn"],
        "TTS#Quản lý khách sạn": ["Quản lý khách sạn"],
        "TTS#Hành lý khách sạn": ["Hành lý khách sạn"],
        "TTS#Lưu trú khách sạn": ["Lưu trú khách sạn"],
        "TTS#Điều dưỡng, hộ lý": ["Điều dưỡng, hộ lý"],
    },


    "INSIGHT" : {
        "Nhà xưởng" : ["nhà xưởng", "xưởng", "nhà máy"],
        "yêu cầu bằng lái" : ["yêu cầu bằng lái", "bằng lái"],
        "Có thưởng" : ["thưởng", "có thưởng"],
        "Dễ cày tiền" : [ "cày tiền"],
        "Kinh nghiệm" : ["kinh nghiệm", "có kinh nghiệm", "có kn"],
        "Không cần tiếng" : ["không cần tiếng", "không yêu cầu tiếng"],
        "Không làm đêm" : ["không làm đêm", "không ca đêm"],
        "Hỗ trợ chỗ ở" : ["chỗ ở", "hỗ trợ chỗ ở"],
        "Tăng ca" : ["tăng ca", "tc"],
    },

    "Vùng/Tỉnh/Thành phố" : {
        "Hokkaido" : ["Hokkaido"],"Tohaku" : ["Tohaku"],"Aomori" : ["Aomori"], "Iwate" : ["Iwate"],"Miyagi" : ["Miyagi"], "Akita" : ["Akita"],"Yamagata" : ["Yamagata"],
        "Fukushima" : ["Fukushima"],"Ibaraki" : ["Ibaraki"],"Tochigi" : ["Tochigi"],"Gunma" : ["Gunma"],"Saitama" : ["Saitama"],"Chiba" : ["Chiba"],
        "Tokyo" : ["Tokyo"],"Kanagawa" : ["Kanagawa"],"Niigata" : ["Niigata"], "Toyama" : ["Toyama"],"Ishikawa" : ["Ishikawa"],
        "Fukui" : ["Fukui"],"Yamanashi" : ["Yamanashi"],"Nagano" : ["Nagano"],"Gifu" : ["Gifu"],"Shizuoka" : ["Shizuoka"],
        "Aichi" : ["Aichi"],"Mie" : ["Mie"],"Shiga" : ["Shiga"],"Kyoto" : ["Kyoto"],"Osaka" : ["Osaka"],"Hyogo" : ["Hyogo"],"Nara" : ["Nara"],"Wakayama" : ["Wakayama"],"Tottori" : ["Tottori"],
        "Shimane" : ["Shimane"],"Okayama" : ["Okayama"],"Hiroshima" : ["Hiroshima"],"Yamaguchi" : ["Yamaguchi"],"Tokushima" : ["Tokushima"],"Kagawa" : ["Kagawa"],
        "Ehime" : ["Ehime"],"Kochi" : ["Kochi"],"Fukuoka" : ["Fukuoka"],"Saga" : ["Saga"],"Nagasaki" : ["Nagasaki"],"Kumamoto" : ["Kumamoto"],"Õita" : ["Õita"],
        "Miyazaki" : ["Miyazaki"],"Kagoshima" : ["Kagoshima"],"Okinawa" : ["Okinawa"],
    },
}

# Hàm phân loại nội dung tin nhắn
def classify_content(content, keyword_dict):
    for category, words in keyword_dict.items():
        for word in words:
            if word.lower() in content.lower():
                return category
    return ""

# Hàm trích xuất văn bản từ ảnh
def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='vie')
        return text
    except Exception as e:
        print(f"Lỗi khi trích xuất văn bản từ ảnh: {e}")
        return ""
    
# Hàm lưu ảnh blob từ URL
def dowload_blob_image(driver, blob_url, filename):
    try:
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)

        js_script = """
        var blob_url = arguments[0];
        return fetch(blob_url)
            .then(response => response.blob())
            .then(blob => new Promise((resolve, reject) => {
                var reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            }));
        """
        base64_data = driver.execute_script(js_script, blob_url)
        base64_str = base64_data.split(",")[1]

        img_data = base64.b64decode(base64_str)
        file_path = os.path.join("temp_images", filename)
        with open(file_path, 'wb') as f:
            f.write(img_data)
        print(f"Đã lưu ảnh blob: {file_path}")
        return file_path
    except Exception as e:
        print(f"Lỗi khi lưu ảnh blob: {e}")
        return None

# Hàm lấy link nhóm zalo
def fetch_group_link():
    global group_link
    try:
        avatar_elements = browser.find_elements(By.CLASS_NAME, "threadChat__avatar.clickable")
        if avatar_elements:
            avatar_elements[0].click()
            time.sleep(1)  # Giảm thời gian chờ

            link_elements = browser.find_elements(By.XPATH, '//div[@class="pi-group-profile-link__link"]')
            if link_elements:
                group_link = link_elements[0].text.strip()
                print(f"Link nhóm Zalo: {group_link}")
                time.sleep(2) 
                close_button = WebDriverWait(browser, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.modal-header-icon.icon-only")))
                close_button.click()
                return group_link
        print("Không tìm thấy link nhóm.")
        return ""
    except Exception as e:
        print(f"Lỗi khi lấy link nhóm Zalo: {e}")
        return ""

def scroll_and_click_groups(browser, interval=20):
    try:
        groups = browser.find_elements(By.XPATH, "//div[contains(@class, 'msg-item')]")
        for group in groups:
            group.click()
            fetch_group_link()
            fetch_message_zalo()
            time.sleep(5)
    except Exception as e:
        print(f"Lỗi rồi huấn ơi")


# Hàm lưu dữ liệu vào file excel
def append_row_to_excel(values, file_path="hiepmeo.xlsx"):
    columns = ["Nhóm", "Nội dung", "Phân loại tin", "Loại hình visa", "Trình độ ngoại ngữ", "Giới tính", "Ngành", "Công việc chi tiết", "INSIGHT", "Vùng/Tỉnh/Thành phố", "Lương yên/giờ", "Lương cơ bản/tháng", "Lương về tay/tháng", "Người đăng", "Thời gian", "Ngày tháng năm", "Link nhóm"]

    if os.path.exists(file_path):
        existing_data = pd.read_excel(file_path)            
        updated_data = pd.concat([existing_data, pd.DataFrame([values], columns=existing_data.columns)], ignore_index=True)
        
    else:
        updated_data = pd.DataFrame([values], columns=columns)

    updated_data.to_excel(file_path, index=False)
    print(f"Dữ liệu đã được lưu vào {file_path}")

# Hàm thu thập tin nhắn từ Zalo
def fetch_message_zalo():
    time.sleep(15)
    try:
        chat_items = browser.find_elements(By.CLASS_NAME, 'chat-item')
        group_names = browser.find_element(By.CLASS_NAME, 'header-title')
        group_name = group_names.text.replace("&nbsp", ' ')
        print(f"Đang thu thập dữ liệu từ nhóm: {group_name}")
        global unique_messages

        for chat_item in chat_items:
            try:
                sender_name = chat_item.find_element(By.XPATH, '//div[@class="message-sender-name-content clickable"]/div[@class="truncate"]')
                user_name = sender_name.text.replace("&nbsp", ' ')
            except:
                user_name = "khong ro"


            messages = chat_item.find_elements(By.CSS_SELECTOR, '[data-component="message-text-content"]')
            images = chat_item.find_elements(By.XPATH, ".//div[@class='image-box__image']/img")
            
            if messages:
                message_text = messages[0].text
                if message_text and message_text not in unique_messages:
                    unique_messages.add(message_text)

                    phân_loại_tin = classify_content(message_text, keywords["phân loại tin"])
                    loại_hình_visa = classify_content(message_text, keywords["Loại hình visa"])
                    công_việc_chi_tiết = classify_content(message_text, keywords["Công việc chi tiết"])
                    trình_độ_ngoại_ngữ = classify_content(message_text, keywords["Trình độ ngoại ngữ"])
                    insight = classify_content(message_text, keywords["INSIGHT"])
                    giới_tính = classify_content(message_text, keywords["Giới tính"])
                    ngành = ""
                    vùng_tỉnh_thành = classify_content(message_text, keywords["Vùng/Tỉnh/Thành phố"])
                    luong_yen_gio = re.findall(r'(\d+)\s*y/h', message_text, re.IGNORECASE)
                    luong_yen_gio = luong_yen_gio[0] if luong_yen_gio else None
                    luong_cb_man = re.findall(r'(?:lcb|lương cơ bản|lương|luong co ban|LCB:)\s*(\d+)', message_text, re.IGNORECASE)
                    luong_cb_man = luong_cb_man[0] if luong_cb_man else None
                    luong_vt_man = re.findall(r'(?:lương thực lĩnh|lvt|lương về tay|luong thuc linh)\s*(\d+)', message_text, re.IGNORECASE)
                    luong_vt_man = luong_vt_man[0] if luong_vt_man else None
                    thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    thoi_gian_parsed = datetime.strptime(thoi_gian, "%Y-%m-%d %H:%M:%S")
                    timestamp = int(thoi_gian_parsed.timestamp())
                    ngay_thang_nam = datetime.now().strftime("Ngày %d Tháng /%m Năm /%Y")
                    new_row = [group_name, message_text, phân_loại_tin, loại_hình_visa, trình_độ_ngoại_ngữ, giới_tính, ngành,
                            công_việc_chi_tiết, insight, vùng_tỉnh_thành,luong_yen_gio, luong_cb_man, luong_vt_man,
                            user_name, timestamp, ngay_thang_nam, group_link]
                    append_row_to_excel(new_row)

            
            if images:
                for idx, img in enumerate(images):
                    img_src = img.get_attribute("src")
                    local_image_path = None

                    if img_src in processed_images:
                        print(f"Ảnh đã được xử lý: {img_src}")
                        continue

                    # Xử lý blob URL
                    if img_src.startswith("blob:"):
                        print(f"Đang tải ảnh blob: {img_src}")
                        local_image_path = dowload_blob_image(browser, img_src, f"blob_image_{idx}.jpg")

                    # Xử lý URL HTTP/HTTPS
                    elif img_src.startswith("http"):
                        print(f"Đang tải ảnh: {img_src}")
                        response = requests.get(img_src, stream=True)
                        if response.status_code == 200:
                            local_image_path = f"temp_image_{idx}.jpg"
                            with open(local_image_path, "wb") as f:
                                f.write(response.content)

                    if local_image_path:
                        processed_images.add(img_src)
                        message_text = extract_text_from_image(local_image_path)

                        if message_text and message_text not in unique_messages:
                            unique_messages.add(message_text)
                            
                            giới_tính = classify_content(message_text, keywords["Giới tính"])
                            công_việc_chi_tiết = classify_content(message_text, keywords["Công việc chi tiết"])
                            phân_loại_tin = classify_content(message_text, keywords["phân loại tin"])
                            loại_hình_visa = classify_content(message_text, keywords["Loại hình visa"])
                            trình_độ_ngoại_ngữ = classify_content(message_text, keywords["Trình độ ngoại ngữ"])
                            insight = classify_content(message_text, keywords["INSIGHT"])
                            giới_tính = classify_content(message_text, keywords["Giới tính"])
                            ngành = ""
                            vùng_tỉnh_thành = classify_content(message_text, keywords["Vùng/Tỉnh/Thành phố"])
                            luong_yen_gio = re.findall(r'(\d+)\s*y/h', message_text, re.IGNORECASE)
                            luong_yen_gio = luong_yen_gio[0] if luong_yen_gio else None
                            luong_cb_man = re.findall(r'(?:lcb|lương cơ bản|luong co ban)\s*(\d+)', message_text, re.IGNORECASE)
                            luong_cb_man = luong_cb_man[0] if luong_cb_man else None
                            luong_vt_man = re.findall(r'(?:lương thực lĩnh|lvt|lương về tay|luong thuc linh)\s*(\d+)', message_text, re.IGNORECASE)
                            luong_vt_man = luong_vt_man[0] if luong_vt_man else None
                            thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            thoi_gian_parsed = datetime.strptime(thoi_gian, "%Y-%m-%d %H:%M:%S")
                            timestamp = int(thoi_gian_parsed.timestamp())
                            ngay_thang_nam = datetime.now().strftime("Ngày %d Tháng /%m Năm /%Y")

                            # Lưu vào Excel
                            new_row = new_row = [group_name,message_text, phân_loại_tin, loại_hình_visa, trình_độ_ngoại_ngữ, giới_tính, ngành,
                            công_việc_chi_tiết, insight, vùng_tỉnh_thành,luong_yen_gio, luong_cb_man, luong_vt_man, 
                            user_name, timestamp, ngay_thang_nam, group_link]
                            append_row_to_excel(new_row)

                        os.remove(local_image_path) 

    except Exception as e:
        print(f"Chưa click vào nhóm")
              
print("Bắt đầu thu thập dữ liệu...")
while True:
    scroll_and_click_groups(browser)
    time.sleep(5)