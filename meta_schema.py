VISA_JOB_KEYWORDS = {
    "Thực tập sinh 3 năm": [
        'tr/F', 'tr/f', 'triệu/form', 'tr/form', 'mua form', 'mua ...tr', 'cc', 'mg', 'bay gấp', 'phí tổng', 'gửi form',
        'cơ chế', 'xăm', 'nhận xăm kín', 'xăm nhỏ', 'xăm lớn', 'xăm to', 'nhận xăm', 'NHẬN XĂM HỞ', 'vgb', 'viêm gan B', 'trực tiếp',
        'bảng lương', 'ra tết học', 'học ngoài', 'học ngoại', 'x lấy y', 'thi'
    ],
    "Thực tập sinh 1 năm": [
        "1 năm", "1n"
    ],
    "Thực tập sinh 3 go": [
        "may 3go", "may 3 go", "3go", "3 go", 'may quay lại'
    ],
  
}
CAREER_NOTE = """Nông nghiệp'; 'Thực phẩm'; 'In ấn'; 'Sơn'; 'Đồ gia dụng'; 'Đóng sách'; 'Đúc'; 'Hàn xì'; 'Đóng gói'; 'Sản xuất hộp'; 'Gốm'; 'Bê tông'; 'Rác thải'; 'Đường sắt'; 'Cao su, nhựa'; 'Vật liệu composite'; 'Nghề Mộc'; 'Ngư nghiệp'; 'Dệt may'; 'Xây dựng'; 'Cơ khí, kim loại'; 'Sân bay'; 'Nồi hơi'; 'Logistic'; 'Vận chuyển'; 'Điều dưỡng'; 'Chế tạo vật liệu'; 'Đóng tàu'; 'Nhà hàng'; 'Vệ sinh toà nhà'; 'Buồng phòng khách sạn'; 'Chế tạo máy'; 'Ô tô'; 'Lưu trú', 'Khách sạn'; 'Vận tải', 'Lái xe'; 'Điện, điện tử'; 'Kiến trúc'; 'Tài chính', 'Bảo hiểm'; 'Thiết kế'; 'Công nghệ thông tin'; 'Bảo trì, sửa chữa máy móc'; 'Quản lý sản xuất'; 'Giải trí', 'Du lịch'; 'Kế toán'; 'Kinh doanh, Sale, Tiếp thị'; 'Y tế'; 'Năng lượng';'Phiên dịch viên';'Giặt là'.\n
                    * Note: 
                    - 'nntt'->'Nông nghiệp trồng trọt', 'lmxd' -> 'Lái máy xây dựng\n
                    - 'cbtp','cctp','tp'->'Thực phẩm' , 'dgcn' -> 'Đóng gói công nghiệp'\n
                    - 'ks may'->'Dệt may'\n
                    - 'lmxd' -> 'Lái máy xây dựng', 'lk điện tử' -> 'linh kiện điện tử', 'lkđt' -> 'linh kiện điện tử'\n
                    - 'front'->'Khách sạn', 'nh' -> 'nhà hàng', 'nncn' -> 'nông nghiệp chăn nuôi'\n
                    - 'hàn bán tự động'->'Hàn xì', 'htnt' -> 'hoàn thiện nội thất'\n
                    - 'hàn btđ'->'Hàn bán tự động'\n
                    - 'kaigo'->'Điều dưỡng'\n
                    - 'vận hành máy','GCCK','vhm','nhóm 1','nhóm ngành 1','nhóm 2','nhóm ngành 2','đgcn'->'Cơ khí, kim loại'\n
                    - 'nội thất','dán giấy','đường ống'->'Xây dựng'\n
                    If unavailable -> 'Empty'."""
META_JOB_SCHEMA = {
    "name": "job",
    "strict": True,
    "schema": {
            "type": "object",
            "description": "Return raw JSON only, without adding ``` or any other formatting or any other AI content",
            "properties": {
                "postType": {
                    "type": "string",
                    "description": """Phân loại nội dung tin đầu vào chỉ lấy dữ liệu thực tập sinh.
                    - Nếu có các từ liên TKT, KS, tokutei, kĩ sư, nội dung không phải nước nhật bản (hàn quốc, đài loan..), không liên quan đến tuyển dụng => 'Tin rác'.
                    - Nếu không phân loại được trả về 'VIỆC LÀM NHẬT'.
                    """,
                    "enum": ["VIỆC LÀM NHẬT", "Tin rác"]
                },
                "visa": {
                    "type": "string",
                    "description": f"""- Dưới đây là danh sách tiêu đề và từ khóa liên quan:\n
                    {VISA_JOB_KEYWORDS}\n
                    - Lưu ý: \n
                        + các từ viết tắt đ.Việt -> đầu Việt, đ.Nhật -> đầu Nhật, tts -> thực tập sinh\n
                        + Nếu nội dung có có dạng như 'Phí A-B-C' -> Thực tập sinh 3 năm\n
                        + Nếu nội dung có nhắc đến ngày phỏng vấn , ngày thi tuyển -> Thực tập sinh 3 năm\n 
                    - Yêu cầu:\n
                    Phân tích nội dung input để tìm ra loại visa xklđ(thường là Nhật Bản) phù hợp.\n
                    Đối chiếu các từ khóa có trong input với danh sách từ khóa của từng tiêu đề và kết hợp với lưu ý, ưu tiên các trường hợp đặc biệt có trong lưu ý.\n
                    Xác định tiêu đề nào chứa nhiều từ khóa phù hợp hoặc liên quan nhất với input.\n
                    - Output: Bắt buộc phải chọn ra 1 tiêu đề phù hợp nhất từ danh sách đã đưa và trả về. không bao gồm câu từ AI. nếu không có từ khóa rõ ràng trả về 'thực tập sinh 3 năm' """,
                        "enum": ["Thực tập sinh 3 năm", "Thực tập sinh 1 năm", "Thực tập sinh 3 go"]
                    },
                "job": {
                    "type": "string",
                    "description": "bất cứ ngành nghề , công việc nào được nhắc đến trong nội dung tin nhắn , tham khảo nếu xuất hiện từ khóa viết tắt trong {CAREER_NOTE}. Nếu không có công việc nào thì trả về 'Không cung cấp'."
                },

                "workLocation": {
                    "type": "string",
                    "description": "Trả về bất cứ tỉnh, thành phố, khu vực nào được nhắc đến trong đơn hàng. Nếu không có thông tin về địa điểm làm việc thì trả về 'Empty'.",
                },

                "interviewFormat": {
                    "type": "string",
                    "description": "Nếu nội dung có nhắc đến phần phỏng vấn Online thì trả về 'Online', nếu không nhắc đến thì để mặc định là 'Trực tiếp'",
                    "enum": ["Online", "Trực tiếp"]
                },

                "languageLevel": {
                    "type": "string",
                    "description": "Trình độ ngoại ngữ trong đơn nếu có nhiều N4,N3,N2 thì chọn N thấp nhất. Có các từ khóa như 'ko yc tiếng', 'không tiếng' => 'Không yêu cầu tiếng' ."
                    "nếu không có trình độ ngôn ngữ nào thì trả về 'Không cung cấp'.",
                    "enum": ["Không yêu cầu tiếng","JLPT N5", "JLPT N4", "JLPT N3", "JLPT N2", "JLPT N1", "Kaiwa N5", "Kaiwa N4", "Kaiwa N3", "Kaiwa N2", "Kaiwa N1", "Kaiwa N1", "Kaiwa N1", "Không cung cấp"]

                },
                "hourlyWage": {
                    "type": "string",
                    "description": """Mức lương theo giờ của đơn hàng.
                     - Chỉ lấy con số, không lấy kèm đơn vị tiền tệ.
                     - đơn hàng  có cụm 1s5 => 1500 yên/giờ, 1300h => 1300 yên/giờ.
                     - nếu trong đơn có các cụm '1400', '1350' , '1300' => lương theo giờ (yên/giờ).
                     - nếu trong đơn có '20tr/f', '20tr/form', '1400-15-5300', '25-35%/1h' => không phải lương.
                     - nếu không có nhắc tới lương theo giờ => 'Empty'
                    """,
                },

                "basicSalary": {
                    "type": "string",
                    "description": """Mức lương cơ bản của đơn hàng.
                     - Chỉ lấy con số, không lấy kèm đơn vị tiền tệ.
                     - nếu trong đơn có 20tr/f, 20tr/form, '1400-15-5300', 25-35%/1h  => không phải lương.
                     - nếu đơn hàng ghi như 'lcb 26', 'lương cơ bản', '18m', 'lương 18', 'lg 21-25m' ... => đó là lương cơ bản (man/tháng).
                     - nếu lương có khoảng như '20-25 man', thì lấy số đứng trước dấu '-'
                     - nếu trong đơn có khoảng lương cao ví dụ'500-700' => đó là lương năm. lấy số đứng trước dấu '-' chia cho 12 để chuyển về lương tháng.
                     - nếu không có nhắc tới lương cơ bản => 'Empty'
                     """,
                  
                },
                "realSalary": {
                    "type": "string",
                    "description": """Mức lương thực lĩnh (lương về tay) của đơn hàng.
                     - Chỉ lấy con số, không lấy kèm đơn vị tiền tệ.
                     - nếu trong đơn có '20tr/f', '20tr/form', '1400-15-5300', '25-35%/1h', 'TC 30-40h'  => không phải lương.
                     - nếu đơn hàng ghi như 'ltl 26', 'lương thực lĩnh', 'về tay'... => đó là lương thực lĩnh (man/tháng).
                     - nếu không có nhắc tới lương thực lĩnh => 'Empty'
                     """,
                
                },
              
                "candidates": {
                    "type": "string",
                    "description": """Số lượng thi tuyển
                                nếu trong đơn có ghi số lượng thi tuyển ghi là 6 => 6. Nếu không có nhắc tới số lượng thi tuyển => 'Empty'
                                """,
                },
                "success-candidate": {
                    "type": "string",
                    "description": """Số lượng trúng tuyển
                                    nếu trong đơn ghi số lượng trúng tuyển ghi là 3 => 3. Nếu không có nhắc tới số lượng trúng tuyển => 'Empty'
                                    """,
                },
                "phone": {
                    "type": "string",
                    "description": """nếu trong đơn có Số điện thoại, liên hệ ví dụ '0936413792' => '0936413792' hiển thị cả số 0. Nếu không thấy nhắc tới số điện thoại => 'Empty'""",
                },

                "date": {
                    "type": "string",
                    "description": """ngày phỏng vấn trong đơn hàng nếu có ví dụ '24/02' ghi 'ngày 24 tháng 2'. Nếu không có nhắc tới ngày phỏng vấn => 'Empty'""",
                },

                "phi": {
                    "type": "number",
                    "description": "đơn hàng có ghi 'Phí: 5600-1200-3tr', '5600-1000-17', '56-14', 'Phí 5,6k' => '5600' hoặc Nếu chỉ ghi 'phí 5000' => '5000'. Nếu không có phí => 'Empty'"
                },  
                "back": {
                    "type": "number",
                    "description": "đơn hàng có ghi 'Phí: 5600-1200-3tr', '5000-1200-10', '40-12' => '1200'. Nếu chỉ ghi '5400-2000' => '2000'. Nếu không có phí => 'Empty'"
                },

                "coche": {
                    "type": "number",
                    "description":  "đơn hàng có ghi 'Phí: 5600-1200-3tr', '5000-1000-3 triệu', '5000-1000-3'=> '3.0000.000', các đơn có ghi 15tr/form , 15 triệu/form, 15tr/f, ghi 15tr ở đầu nội dung => 15000000. Nếu chỉ ghi '5400-2000' => 'Empty'. Nếu không có phí => 'Empty'"
                },


                "gender": {
                    "type": "string",
                    "description": """Giới tính yêu cầu
                    - Nam nếu chỉ yêu cầu nam
                    - Nữ nếu chỉ yêu cầu nữ
                    - Cả Nam và Nữ nếu trong đơn có cả nam và nữ
                    """,
                    "enum": ["Nam", "Nữ", "Cả Nam và Nữ", 'Không cung cấp']
                },
              
               "specialConditions": {
                    "type": "array",
                    "description": """Trả về mảng các lựa chọn. Nếu có nhiều giá trị khác nhau, nối với nhau bởi dấu ';' (ví dụ: 'Tăng ca;Lương tốt').
                    Các trường hợp cụ thể:
                    - Nếu có nhắc đến 'tăng ca', 'tg ca', 'tca', 'tc', 'ot' hay làm thêm giờ thì kết quả trả về phải có 'Tăng ca'.
                    - Nếu có từ 'tiến cử', 'bao đậu' thì trả về 'Bao đỗ'.
                    - Nếu có từ 'thưởng', 'thg' thì trả về 'Thưởng'.
                    - Nếu có cụm từ 'lương cao' thì trả về 'Lương tốt'.
                    - Nếu có nhắc đến 'vợ chồng' thì trả về 'Vợ chồng'.
                    - Nếu có nhắc đến 'không yêu cầu kinh nghiệm', 'ko yc kn'thì trả về 'không yêu cầu kinh nghiệm'.
                    - Nếu có nhắc đến 'hỗ trợ chỗ ở' thì trả về 'Hỗ trợ chỗ ở'.
                    - Không trả về giá trị nếu từ khóa không xuất hiện trong nội dung.
                    - không trả về các giá trị trùng lặp trong mảng, một giá trị chỉ xuất hiện 1 lần.
                    """,
                    "items": {
                        "type": "string",
                        "enum": ["Bao đỗ", "Tăng ca", "Lương tốt", "Vợ chồng", "Hỗ trợ chỗ ở", "không yêu cầu kinh nghiệm", "Thưởng"]
                    },
                },
               "makeAI": {
                     "type": "string",
                    "description": """Mô tả đơn hàng chuẩn hóa bằng tiếng Việt, giữ nguyên nội dung chính, theo mẫu:  
                    'Nông nghiệp - Chiba: Tuyển nam (20-33 tuổi). Công việc: trồng trọt. Lương về tay 20 man/tháng. Phỏng vấn 24/02. Nhận xăm nhỏ kín.'  

                    - **Loại bỏ:** Từ viết tắt, thông tin quảng cáo, số điện thoại. \n
                    - **Chỉ giữ lại:** Các thông tin quan trọng như ngành nghề, địa điểm, độ tuổi, công việc, lương, ngày phỏng vấn, yêu cầu đặc biệt (xăm, VGB). \n
                    - **Không được trả về 'không cung cấp'.** Nếu một trường thông tin không có, **bỏ qua**, không ghi gì thay thế.  \n
                    - **Định dạng đúng theo mẫu**, không tự động thêm thông tin không có trong dữ liệu. """, 
                },
            },
        "required": [
                "postType",
                "visa",
                "languageLevel",
                "gender",
                "job",
                "specialConditions",
                "workLocation",
                "hourlyWage",
                "basicSalary",
                "realSalary",
                "candidates",
                "success-candidate",
                "phone",
                "date",
                "phi",
                "back",
                "coche",
                "interviewFormat",
                "makeAI",
            ],
        "additionalProperties": False
    }
}



