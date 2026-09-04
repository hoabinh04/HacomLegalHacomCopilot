from typing import Dict, Any, List
from knowledge_graph import LegalKnowledgeGraph

class LegalAlertEngine:
    """
    Động cơ Đánh giá Tác động Pháp luật Đa Chiều (Multi-tier Legal Impact Assessment Engine).
    Phân loại chuẩn xác 4 Mức độ Tác động:
      🔴 Mức Đỏ (Khẩn cấp / Rủi ro pháp lý & Chi phí cao)
      🟡 Mức Vàng (Cảnh báo nghiệp vụ / Cần rà soát quy trình)
      🟢 Mức Xanh Lá (Thuận lợi / Tháo gỡ khó khăn & Ưu đãi)
      🔵 Mức Xanh Lam (Thông tin / Bổ sung hướng dẫn & Lưu trữ)
    """

    def __init__(self):
        self.kg = LegalKnowledgeGraph()
        # 5 Nhóm Lĩnh vực Dự án Cốt lõi của HACOM
        self.project_types_info = [
            {"id": "KDT", "name": "Dự án Khu đô thị & BĐS thương mại", "type": "KĐT", "stage": "Bồi thường GPMB & Thẩm định giá đất cụ thể"},
            {"id": "NOXH", "name": "Dự án Nhà ở xã hội & Nhà ở công nhân", "type": "NOXH", "stage": "Thẩm định giá bán & Cấp sổ hồng"},
            {"id": "NLTT", "name": "Dự án Năng lượng tái tạo & Điện gió", "type": "NLTT", "stage": "Thỏa thuận PPA & Vận hành thương mại COD"},
            {"id": "ND", "name": "Dự án BĐS nghỉ dưỡng & Khách sạn", "type": "ND", "stage": "Thuê đất thương mại dịch vụ & ĐTM bảo vệ bờ biển"},
            {"id": "CCN", "name": "Dự án Cụm công nghiệp & Hạ tầng kỹ thuật", "type": "CCN", "stage": "Thành lập CCN & Xử lý nước thải tập trung"}
        ]

    def assess_new_law_impact(self, new_doc_num: str, new_doc_title: str, target_field: str = "Chung") -> Dict[str, Any]:
        """
        Phân tích ma trận tác động đa chiều dựa trên từ khóa bản chất văn bản và lĩnh vực chuyên môn.
        """
        title_lower = (new_doc_title or "").lower()
        num_lower = (new_doc_num or "").lower()
        field_lower = (target_field or "").lower()
        combined_text = f"{num_lower} {title_lower} {field_lower}"

        severity = "🔵 Mức Xanh Lam (Thông tin - Bổ sung hướng dẫn nghiệp vụ thông thường)"
        severity_code = "blue"
        affected_projects = []
        recommended_action = "Lưu trữ văn bản vào kho tri thức pháp lý, theo dõi biểu mẫu hướng dẫn chi tiết của các Sở/Ngành liên quan."

        # 1. KIỂM TRA MỨC XANH LÁ: Tháo gỡ khó khăn, Nới điều kiện, Ưu đãi, Gia hạn
        if any(k in combined_text for k in ["tháo gỡ", "ưu đãi", "nới điều kiện", "gia hạn", "miễn giảm", "nghị quyết 33", "đơn giản hóa", "hỗ trợ doanh nghiệp"]):
            severity = "🟢 Mức Xanh Lá (Thuận lợi - Chính sách tháo gỡ vướng mắc & Mở rộng cơ chế ưu đãi)"
            severity_code = "green"
            if "nhà ở" in combined_text or "noxh" in combined_text or "100/2024" in combined_text or "136/2026" in combined_text:
                affected_projects = [p for p in self.project_types_info if p["type"] == "NOXH"]
                recommended_action = "Tận dụng ngay cơ chế nới lỏng điều kiện thu nhập và đơn giản hóa thủ tục hồ sơ để đẩy nhanh tốc độ bán hàng và xét duyệt đối tượng mua nhà ở xã hội."
            else:
                affected_projects = [p for p in self.project_types_info if p["type"] in ["KĐT", "NOXH", "NLTT"]]
                recommended_action = "Áp dụng cơ chế tháo gỡ khó khăn về dòng tiền và quy trình phê duyệt pháp lý để đẩy nhanh tiến độ triển khai dự án."

        # 2. KIỂM TRA MỨC ĐỎ: Khẩn cấp / Rủi ro pháp lý & Thay đổi chi phí lớn (Bảng giá đất mới, Thặng dư, Thu hồi đất vi phạm, Đấu thầu đất)
        elif any(k in combined_text for k in ["bảng giá đất", "bỏ khung giá", "định giá đất thặng dư", "thu hồi đất do vi phạm", "hủy thầu", "71/2024", "88/2024", "103/2024", "tiền sử dụng đất"]):
            severity = "🔴 Mức Đỏ (Khẩn cấp - Tác động lớn đến Nghĩa vụ Tài chính, Giá đất & GPMB)"
            severity_code = "red"
            affected_projects = [p for p in self.project_types_info if p["type"] in ["KĐT", "ND", "CCN"]]
            recommended_action = "Ban Pháp chế & Ban Tài chính rà soát khẩn cấp Phương án Bồi thường GPMB, tính toán lại Suất vốn đầu tư và Tiền sử dụng đất theo 4 phương pháp định giá đất mới của Nghị định 71/2024/NĐ-CP."

        # 3. KIỂM TRA MỨC VÀNG: Cảnh báo nghiệp vụ (PCCC QCVN 06, Cơ chế DPPA điện lực, Đấu thầu M3, Môi trường ĐTM, Tiêu chuẩn chất lượng xây dựng)
        elif any(k in combined_text for k in ["pccc", "phòng cháy", "qcvn 06", "50/2024", "dppa", "80/2024", "mua bán điện", "đấu thầu", "115/2024", "m3", "đtm", "môi trường", "xử lý nước thải", "32/2024", "15/2021", "35/2023", "quản lý chất lượng"]):
            severity = "🟡 Mức Vàng (Cảnh báo - Yêu cầu rà soát quy trình, định mức & Tiêu chuẩn kỹ thuật)"
            severity_code = "yellow"
            
            if "pccc" in combined_text or "phòng cháy" in combined_text or "06" in combined_text:
                affected_projects = self.project_types_info
                recommended_action = "Cập nhật hồ sơ thiết kế cơ sở và giải pháp phòng cháy chữa cháy theo Quy chuẩn QCVN 06:2022 và NĐ 50/2024/NĐ-CP trước khi trình thẩm duyệt."
            elif "điện" in combined_text or "dppa" in combined_text or "80" in combined_text:
                affected_projects = [p for p in self.project_types_info if p["type"] == "NLTT"]
                recommended_action = "Rà soát điều kiện tham gia cơ chế mua bán điện trực tiếp DPPA qua lưới quốc gia và cấu trúc Hợp đồng kỳ hạn Forward theo Nghị định 80/2024."
            elif "đấu thầu" in combined_text or "115" in combined_text:
                affected_projects = [p for p in self.project_types_info if p["type"] in ["KĐT", "ND"]]
                recommended_action = "Rà soát hồ sơ mời thầu và tiêu chuẩn đánh giá hiệu quả sử dụng đất (M3) theo Nghị định 115/2024/NĐ-CP."
            else:
                affected_projects = [p for p in self.project_types_info if p["type"] == "CCN"]
                recommended_action = "Cập nhật quy chuẩn bảo vệ môi trường, chỉ tiêu kỹ thuật và hệ thống xử lý nước thải theo Nghị định 32/2024/NĐ-CP."

        # 4. MỨC MẶC ĐỊNH (THÔNG BÁO THÔNG THƯỜNG)
        else:
            if "đất" in combined_text:
                affected_projects = [p for p in self.project_types_info if p["type"] == "KĐT"]
            elif "nhà ở" in combined_text:
                affected_projects = [p for p in self.project_types_info if p["type"] == "NOXH"]
            else:
                affected_projects = self.project_types_info[:2]

        return {
            "new_law": {"number": new_doc_num, "title": new_doc_title, "field": target_field},
            "severity": severity,
            "severity_code": severity_code,
            "affected_projects": affected_projects,
            "recommended_action": recommended_action
        }

if __name__ == "__main__":
    alert_sys = LegalAlertEngine()
    test_cases = [
        ("33/NQ-CP", "Nghị quyết 33/NQ-CP về một số giải pháp tháo gỡ thị trường BĐS", "Đầu tư"),
        ("71/2024/NĐ-CP", "Nghị định 71/2024/NĐ-CP quy định về giá đất", "Đất đai"),
        ("50/2024/NĐ-CP", "Nghị định 50/2024/NĐ-CP về PCCC và cứu nạn", "Xây dựng"),
        ("12/2021/TT-BXD", "Thông tư 12/2021/TT-BXD ban hành định mức xây dựng", "Xây dựng")
    ]
    print("=== KIỂM THỬ PHÂN CẤP MỨC ĐỘ CẢNH BÁO ===")
    for num, title, field in test_cases:
        res = alert_sys.assess_new_law_impact(num, title, field)
        print(f" • [{num}] -> {res['severity']}")
