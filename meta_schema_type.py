META_UV_SCHEMA = {
    "name": "job",
    "strict": True,
    "schema": {
        "type": "object",
        "description": "Return raw JSON only, without adding ``` or any orther formatting or any other AI content",
        "properties": {
            "postType": {
                "type": "string",
                "description": """Phân loại nội dung phù hợp theo mẫu:
                "VIỆC LÀM":nếu trong nội dung có từ khóa liên quan đến công việc, lương, ngày phỏng vấn. Một số ví dụ của việc làm "CBTP, TOTTORI 1050y/h Kaiwa n4",
                           hoặc "TKT CBTP - CHIBA, IBARAKI(NAM/N.U). LCB 1166-1226y. Tca 30-40h. Vtay 18-24M. 1ng/p, BONASU 20-30M.Htro gino 2"
                "ỨNG VIÊN: nếu trong nội dung có từ khóa liên quan đến tìm đơn , ứng viên . Một số ví dụ của ứng viên "Em tìm đơn cbtp Mie Aichi Có cc,N4 ạ"
                           hoặc "Em tìm đơn thực phẩm cho nam & nữ .có hỗ trợ nhà ạ"
                "TIN RÁC:  nếu có nhiều công việc trong nội dung đó là tin rác, các trường hợp không thuộc hai loại trên, ví dụ như "Yếu tiếng, sợ Kanji, chưa biết bắt đầu học Ginou2? Nhắn em ngay! Có lộ trình học, tài liệu chuẩn, APP ôn tập, mẹo bám sát đề thật giúp anh/chị đậu dễ dàng!"
                           hoặc "Vận chuyển Việt - Nhật Nhận tất cả loại hàng hoá" hoặc "Ôn luyện Ginou 2 mà chưa có tài liệu, bộ đề . Chưa có app ôn luyện. Sợ kanji. Cần hỗ trợ nhắn mình"
                """,
                "enum": ["VIỆC LÀM NHẬT", "ỨNG VIÊN", "TIN RÁC"],
            },
        },

    "required": [
        "postType",
    ],
    "additionalProperties": False,
    }
}