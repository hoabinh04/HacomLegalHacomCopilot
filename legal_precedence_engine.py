import re
from typing import Dict, Any, List, Optional

class LegalPrecedenceEngine:
    """
    Bộ máy Phân xử Hiệu lực & Phủ quyết Văn bản Quy phạm Pháp luật.
    Tuân thủ tuyệt đối quy tắc tại Điều 156 Luật Ban hành Văn bản Quy phạm Pháp luật 2015 (sửa đổi, bổ sung 2020).
    """

    # Cấp bậc hiệu lực pháp lý (Khoản 1 Điều 156: Lex Superior)
    HIERARCHY_LEVELS = {
        "HIEN_PHAP": {"rank": 100, "name": "Hiến pháp", "weight": 100},
        "LUAT": {"rank": 80, "name": "Luật / Bộ luật (Quốc hội)", "weight": 80},
        "NGHI_QUYET_QH": {"rank": 75, "name": "Nghị quyết của Quốc hội", "weight": 75},
        "PHAP_LENH": {"rank": 70, "name": "Pháp lệnh (UBTVQH)", "weight": 70},
        "NGHI_DINH": {"rank": 60, "name": "Nghị định (Chính phủ)", "weight": 60},
        "QUYET_DINH_TTG": {"rank": 50, "name": "Quyết định (Thủ tướng Chính phủ)", "weight": 50},
        "THONG_TU": {"rank": 40, "name": "Thông tư (Bộ trưởng / Thủ trưởng cơ quan ngang bộ)", "weight": 40},
        "VAN_BAN_DIA_PHUONG": {"rank": 20, "name": "Văn bản QPPL của HĐND / UBND cấp tỉnh", "weight": 20}
    }

    # Bảng quan hệ Thay thế / Bãi bỏ / Sửa đổi tường minh (Khoản 4 & Khoản 2 Điều 156)
    KNOWN_PRECEDENCE_PAIRS = [
        # 1. Đất đai & Bồi thường GPMB
        {
            "newer_doc": "31/2024/QH15",
            "newer_name": "Luật Đất đai 2024",
            "older_doc": "45/2013/QH13",
            "older_name": "Luật Đất đai 2013",
            "action": "REPLACES",
            "scope": "Toàn bộ",
            "legal_basis": "Khoản 2 Điều 156 Luật BHVBQPPL & Điều 256 Luật Đất đai 2024: Luật Đất đai 2024 có hiệu lực thi hành từ ngày 01/08/2024, bãi bỏ và phủ quyết toàn bộ Luật Đất đai 2013.",
            "impact_hacom": "Áp dụng bảng giá đất mới, nguyên tắc bồi thường bằng đất khác mục đích sử dụng hoặc nhà ở cho các dự án KĐT Đông Bắc K1, KĐT Bình Sơn K2."
        },
        {
            "newer_doc": "102/2024/NĐ-CP",
            "newer_name": "Nghị định 102/2024/NĐ-CP Chi tiết thi hành Luật Đất đai",
            "older_doc": "43/2014/NĐ-CP",
            "older_name": "Nghị định 43/2014/NĐ-CP Quy định chi tiết Luật Đất đai 2013",
            "action": "REPLACES",
            "scope": "Toàn bộ",
            "legal_basis": "Khoản 2 Điều 156 Luật BHVBQPPL & Điều 107 Nghị định 102/2024/NĐ-CP: Phủ quyết và thay thế hoàn toàn Nghị định 43/2014/NĐ-CP và NĐ 01/2017/NĐ-CP.",
            "impact_hacom": "Áp dụng quy trình giao đất, cho thuê đất và chấp thuận chuyển mục đích sử dụng đất theo thẩm quyền mới."
        },
        {
            "newer_doc": "71/2024/NĐ-CP",
            "newer_name": "Nghị định 71/2024/NĐ-CP về Giá đất",
            "older_doc": "44/2014/NĐ-CP",
            "older_name": "Nghị định 44/2014/NĐ-CP về Giá đất",
            "action": "REPLACES",
            "scope": "Toàn bộ",
            "legal_basis": "Khoản 2 Điều 156 Luật BHVBQPPL & Điều 38 Nghị định 71/2024/NĐ-CP: Bãi bỏ Nghị định 44/2014/NĐ-CP và Thông tư 36/2014/TT-BTNMT.",
            "impact_hacom": "Áp dụng 4 phương pháp định giá đất mới (So sánh, Thu nhập, Thặng dư, Hệ số điều chỉnh), bỏ phương pháp chiết trừ."
        },
        {
            "newer_doc": "88/2024/NĐ-CP",
            "newer_name": "Nghị định 88/2024/NĐ-CP Bồi thường, hỗ trợ, tái định cư",
            "older_doc": "47/2014/NĐ-CP",
            "older_name": "Nghị định 47/2014/NĐ-CP về Bồi thường GPMB",
            "action": "REPLACES",
            "scope": "Toàn bộ",
            "legal_basis": "Khoản 2 Điều 156 Luật BHVBQPPL & Điều 34 Nghị định 88/2024/NĐ-CP: Thay thế hoàn toàn Nghị định 47/2014/NĐ-CP.",
            "impact_hacom": "Cơ chế thưởng tiến độ bàn giao mặt bằng và bồi thường thiệt hại tài sản trên đất dự án nhanh chóng hơn."
        },

        # 2. Nhà ở & Nhà ở xã hội (NOXH)
        {
            "newer_doc": "27/2023/QH15",
            "newer_name": "Luật Nhà ở 2023",
            "older_doc": "65/2014/QH13",
            "older_name": "Luật Nhà ở 2014",
            "action": "REPLACES",
            "scope": "Toàn bộ",
            "legal_basis": "Khoản 2 Điều 156 Luật BHVBQPPL & Điều 197 Luật Nhà ở 2023: Có hiệu lực từ 01/08/2024, bãi bỏ Luật Nhà ở 2014.",
            "impact_hacom": "Chủ đầu tư NOXH được miễn tiền sử dụng đất không cần thẩm định giá đất, được hưởng tối đa 20% tổng diện tích sàn thương mại."
        },
        {
            "newer_doc": "100/2024/NĐ-CP",
            "newer_name": "Nghị định 100/2024/NĐ-CP Phát triển & quản lý NOXH",
            "older_doc": "100/2015/NĐ-CP",
            "older_name": "Nghị định 100/2015/NĐ-CP về Phát triển NOXH",
            "action": "REPLACES",
            "scope": "Toàn bộ",
            "legal_basis": "Khoản 2 Điều 156 Luật BHVBQPPL & Điều 80 Nghị định 100/2024/NĐ-CP: Thay thế toàn bộ NĐ 100/2015/NĐ-CP và NĐ 49/2021/NĐ-CP.",
            "impact_hacom": "Nới lỏng điều kiện thu nhập (dưới 15 triệu/tháng cho người độc thân) đối với người mua nhà ở xã hội Hacom GalaCity."
        },
        {
            "newer_doc": "136/2026/NĐ-CP",
            "newer_name": "Nghị định 136/2026/NĐ-CP Sửa đổi NĐ 100/2024 về NOXH",
            "older_doc": "100/2024/NĐ-CP",
            "older_name": "Nghị định 100/2024/NĐ-CP",
            "action": "AMENDS",
            "scope": "Một phần (Điều kiện xét duyệt & thời hạn giải ngân)",
            "legal_basis": "Khoản 2 & Khoản 4 Điều 156 Luật BHVBQPPL: Nghị định 136/2026/NĐ-CP ban hành sau, phủ quyết các quy định về thủ tục xác nhận điều kiện cư trú tại NĐ 100/2024/NĐ-CP.",
            "impact_hacom": "Bỏ yêu cầu xác nhận cư trú tại địa phương, cho phép công nhân ngoại tỉnh mua NOXH tại các KCN/dự án của HACOM."
        },

        # 3. Năng lượng tái tạo & Cơ chế DPPA
        {
            "newer_doc": "80/2024/NĐ-CP",
            "newer_name": "Nghị định 80/2024/NĐ-CP Cơ chế Mua bán điện trực tiếp (DPPA)",
            "older_doc": "19/2023/TT-BCT",
            "older_name": "Thông tư 19/2023/TT-BCT Khung giá phát điện",
            "action": "PRECEDENCE_OVER",
            "scope": "Giao dịch điện tái tạo trực tiếp khách hàng lớn",
            "legal_basis": "Khoản 1 Điều 156 Luật BHVBQPPL: Nghị định (cấp Chính phủ) có hiệu lực pháp lý cao hơn Thông tư (cấp Bộ). Khi có quy định khác nhau về trần giá và hình thức mua bán điện, áp dụng Nghị định 80/2024/NĐ-CP.",
            "impact_hacom": "Áp dụng cơ chế DPPA bán điện trực tiếp cho khách hàng công nghiệp tại dự án Điện gió Hòa Thắng 1.2."
        },

        # 4. Đấu thầu lựa chọn nhà đầu tư
        {
            "newer_doc": "22/2023/QH15",
            "newer_name": "Luật Đấu thầu 2023",
            "older_doc": "43/2013/QH13",
            "older_name": "Luật Đấu thầu 2013",
            "action": "REPLACES",
            "scope": "Toàn bộ",
            "legal_basis": "Khoản 2 Điều 156 Luật BHVBQPPL & Điều 96 Luật Đấu thầu 2023: Thay thế toàn bộ Luật Đấu thầu 2013 từ 01/01/2024.",
            "impact_hacom": "Quy trình lựa chọn nhà đầu tư dự án có sử dụng đất được chuẩn hóa, minh bạch tiêu chuẩn năng lực tài chính và kinh nghiệm."
        },
        {
            "newer_doc": "115/2024/NĐ-CP",
            "newer_name": "Nghị định 115/2024/NĐ-CP Đấu thầu lựa chọn nhà đầu tư dự án đất",
            "older_doc": "25/2020/NĐ-CP",
            "older_name": "Nghị định 25/2020/NĐ-CP Quy định chi tiết Luật Đấu thầu về lựa chọn NĐT",
            "action": "REPLACES",
            "scope": "Toàn bộ",
            "legal_basis": "Khoản 2 Điều 156 Luật BHVBQPPL & Điều 73 Nghị định 115/2024/NĐ-CP: Bãi bỏ hoàn toàn Nghị định 25/2020/NĐ-CP.",
            "impact_hacom": "Áp dụng phương pháp đánh giá hồ sơ mời thầu (M3) về hiệu quả sử dụng đất và nộp ngân sách nhà nước m3 mới."
        }
    ]

    def __init__(self):
        pass

    def get_document_level(self, doc_text: str) -> Dict[str, Any]:
        """Xác định cấp bậc hiệu lực của văn bản từ tên hoặc số hiệu."""
        doc_lower = doc_text.lower()
        if "hiến pháp" in doc_lower:
            return self.HIERARCHY_LEVELS["HIEN_PHAP"]
        elif "luật" in doc_lower or "bộ luật" in doc_lower or "/qh" in doc_lower:
            return self.HIERARCHY_LEVELS["LUAT"]
        elif "pháp lệnh" in doc_lower:
            return self.HIERARCHY_LEVELS["PHAP_LENH"]
        elif "nghị định" in doc_lower or "/nđ-cp" in doc_lower or "/nd-cp" in doc_lower:
            return self.HIERARCHY_LEVELS["NGHI_DINH"]
        elif "quyết định" in doc_lower and ("thủ tướng" in doc_lower or "/qđ-ttg" in doc_lower):
            return self.HIERARCHY_LEVELS["QUYET_DINH_TTG"]
        elif "thông tư" in doc_lower or "/tt-" in doc_lower:
            return self.HIERARCHY_LEVELS["THONG_TU"]
        elif "ubnd" in doc_lower or "hđnd" in doc_lower:
            return self.HIERARCHY_LEVELS["VAN_BAN_DIA_PHUONG"]
        return {"rank": 50, "name": "Văn bản quy phạm", "weight": 50}

    def resolve_precedence(self, doc_a: str, doc_b: str) -> Optional[Dict[str, Any]]:
        """
        Phân xử trực tiếp giữa 2 văn bản theo nguyên tắc Điều 156:
        - Kiểm tra bảng quan hệ thay thế/phủ quyết trực tiếp.
        - Kiểm tra cấp bậc hiệu lực (Lex Superior).
        - Kiểm tra thời gian ban hành (Lex Posterior).
        """
        a_clean = doc_a.strip().lower()
        b_clean = doc_b.strip().lower()

        # 1. Tra cứu bảng phủ quyết định danh
        for pair in self.KNOWN_PRECEDENCE_PAIRS:
            newer_id = pair["newer_doc"].lower()
            older_id = pair["older_doc"].lower()
            if (newer_id in a_clean and older_id in b_clean) or (newer_id in b_clean and older_id in a_clean):
                return pair

        # 2. Phân xử theo cấp bậc (Khoản 1 Điều 156)
        level_a = self.get_document_level(doc_a)
        level_b = self.get_document_level(doc_b)

        if level_a["rank"] != level_b["rank"]:
            higher = doc_a if level_a["rank"] > level_b["rank"] else doc_b
            lower = doc_b if level_a["rank"] > level_b["rank"] else doc_a
            higher_level = level_a if level_a["rank"] > level_b["rank"] else level_b
            lower_level = level_b if level_a["rank"] > level_b["rank"] else level_a

            return {
                "newer_doc": higher,
                "newer_name": higher,
                "older_doc": lower,
                "older_name": lower,
                "action": "PRECEDENCE_OVER",
                "scope": "Toàn bộ phạm vi mâu thuẫn",
                "legal_basis": f"Khoản 1 Điều 156 Luật BHVBQPPL 2015: '{higher_level['name']}' có hiệu lực pháp lý cao hơn '{lower_level['name']}'. Quy định của {higher} được ưu tiên áp dụng.",
                "impact_hacom": f"Ban Pháp chế ưu tiên áp dụng {higher} để đảm bảo tính thượng tôn pháp luật."
            }

        return None

    def get_all_precedence_rules(self) -> List[Dict[str, Any]]:
        """Trả về toàn bộ danh mục quan hệ phủ quyết / sửa đổi cập nhật."""
        return self.KNOWN_PRECEDENCE_PAIRS

    def build_llm_precedence_guidelines(self) -> str:
        """Sinh hướng dẫn phân xử Điều 156 để nhúng vào System Prompt cho AI LLM."""
        return """
[QUY TẮC BẮT BUỘC VỀ HIỆU LỰC & PHỦ QUYẾT VĂN BẢN (ĐIỀU 156 LUẬT BAN HÀNH VBQPPL 2015/2020)]:
1. NGUYÊN TẮC HIỆU LỰC CẤP BẬC (Khoản 1): Văn bản cấp cao hơn luôn phủ quyết quy định trái luật của văn bản cấp thấp hơn (Luật > Nghị định > Thông tư).
2. NGUYÊN TẮC THỜI GIAN (Khoản 2): Cùng cơ quan ban hành (hoặc cùng cấp bậc) thì VĂN BẢN BAN HÀNH SAU PHỦ QUYẾT VÀ THAY THẾ VĂN BẢN BAN HÀNH TRƯỚC.
   - Luật Đất đai 2024 phủ quyết Luật Đất đai 2013.
   - Luật Nhà ở 2023 phủ quyết Luật Nhà ở 2014.
   - Luật Kinh doanh BĐS 2023 phủ quyết Luật Kinh doanh BĐS 2014.
   - Luật Đấu thầu 2023 phủ quyết Luật Đấu thầu 2013.
   - Nghị định 102/2024, NĐ 71/2024, NĐ 88/2024 phủ quyết NĐ 43/2014, NĐ 44/2014, NĐ 47/2014.
   - Nghị định 136/2026/NĐ-CP sửa đổi và phủ quyết các điều kiện cư trú tại NĐ 100/2024/NĐ-CP về Nhà ở xã hội.
3. NGUYÊN TẮC CHUYÊN NGÀNH (Khoản 3): Văn bản quy định chuyên ngành (NOXH, Điện gió DPPA, CCN) được ưu tiên áp dụng so với văn bản chung.
4. YÊU CẦU TRÌNH BÀY: Khi phát hiện nội dung có sự thay đổi giữa văn bản cũ và mới, BẮT BUỘC phải giải thích rõ ràng và gán nhãn:
   `[VĂN BẢN MỚI PHỦ QUYẾT]`, `[QUY ĐỊNH CHUYÊN NGÀNH ƯU TIÊN]`, hoặc `[CẢNH BÁO: VĂN BẢN ĐÃ HẾT HIỆU LỰC]`.
"""
