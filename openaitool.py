from openai import OpenAI
from meta_schema import META_JOB_SCHEMA, CAREER_NOTE
from meta_schema_type import META_UV_SCHEMA
import os
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyzeAndSplitJobContent(rawText):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "- Tuyệt đối giữ nguyên nội dung tin nhắn gốc, chỉ chuẩn hóa lại cách viết để dễ đọc và phân tích chính xác hơn.\n" +
                    "- Không được thêm bất kỳ từ, cụm từ, hay nội dung AI nào không có trong tin nhắn gốc.Nếu có từ tiếng nhật thì dịch chuẩn\n" +
                    "- Chỉ thực hiện chuẩn hóa các từ viết tắt, lỗi chính tả, ký tự đặc biệt, hoặc cách ngắt chữ không tự nhiên.\n" +
                    "- lưu ý các từ viết tắt tham khảo ở" + CAREER_NOTE + "\n" +
                    "- ví dụ '$CBTP kanto ợ n.h.a.n n.a.m/n.u @ kai.wa.n2 / s A n..h.ậ..n  đ.unn.g n.gà..nh' → 'chế biến thực phẩm kanto, nhận nam nữ kaiwa n2, nhận đúng ngành'.\n" +
                    "- Giữ nguyên cấu trúc nội dung gốc, không thay đổi ý nghĩa hay thêm suy diễn.\n" +
                    "- Kết quả trả về dưới dạng chuỗi văn bản rõ ràng, không chứa ký tự đặc biệt, lỗi định dạng hoặc JSON.\n" +
                    "- Nếu tin nhắn chứa nội dung quảng cáo, giới thiệu nhóm, hoặc thông tin không liên quan đến tuyển dụng thì loại bỏ chúng.\n" +
                    "- Nếu có thông tin liên hệ (số điện thoại, email, link), hãy giữ nguyên và đặt ở cuối tin nhắn.\n" +
                    "- Nếu không có thông tin liên hệ, không thêm bất kỳ nội dung nào vào cuối.\n" +
                    "- Đầu ra phải là nội dung thuần văn bản, dễ đọc, không chứa từ khóa 'json', dấu ngoặc kép, dấu ngoặc nhọn, hoặc bất kỳ ký tự đặc biệt nào khác.\n" +
                    "- Bắt buộc phải trả về giá trị, không để trống.")
            },
            {
                "role": "system",
                "content": rawText,
            }
        ],
        model="gpt-4.1",
    )
    return chat_completion


def analyzeJobInformation(rawText):
    chat_completion = client.chat.completions.create(
        response_format={
            "type": "json_schema",
            "json_schema": META_JOB_SCHEMA
        },
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là chuyên gia phân tích dữ liệu có 20 năm kinh nghiệm"
                    "Nhiệm vụ của bạn là phân tích nội dung đầu vào và xác định đúng loại visa bằng cách kiểm tra đầy đủ các tiêu chí:"
                    "\n Trước khi phân loại, bạn phải kiểm tra **tất cả từ khóa liên quan** trong nội dung."
                    "\n Nếu một nội dung có tỉnh thành của Nhật Bản, điều đó không có nghĩa là nó là 'đầu Nhật' trừ khi có từ khóa liên quan đến loại visa."
                    "\n không tự động gán loại visa nếu không có thông tin cụ thể."
                    "\nTrả về kết quả JSON theo định dạng yêu cầu. Trả về đúng kết quả schema và không thêm bất kỳ thông tin dư thừa nào")
            },

            {
                "role": "system",
                "content": 'Phân tích nội dung: "'+rawText+'"',
            }
        ],
        model="gpt-4.1",
    )
    return chat_completion

def analysisPostType(rawText):
    chat_completion = client.chat.completions.create(
        response_format={
            "type": "json_schema",
            "json_schema": META_UV_SCHEMA
        },
        messages=[
            {
                "role": "system",
                "content": (
                    """
                    "content": (
                        "Phân loại nội dung thành một trong ba loại: 'VIỆC LÀM NHẬT', 'ỨNG VIÊN' hoặc 'TIN RÁC' dựa vào {META_UV_SCHEMA}\n"
                        "Nếu có nhiều đơn hàng trong một ô nội dung phân loại là 'TIN RÁC'\n"
                        "Các đơn hàng không thuộc nước Nhật Bản , đơn Đài Loan, Hàn quốc... và nội dung không rõ ràng phân loại là 'TIN RÁC'\n"
                        "Trả về JSON đúng định dạng schema, không thêm bất kỳ nội dung nào ngoài kết quả."
                    )                    
                    """
                )
            },
            {
                "role": "system",
                "content": 'Phân tích nội dung: "'+rawText+'"',
            }
        ],
        model="gpt-4.1",
    )
    return chat_completion
