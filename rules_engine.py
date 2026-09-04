from typing import Dict, Any, List

class LegalRulesEngine:
    """
    Rules Engine xử lý quy tắc pháp lý cố định theo Điều 156 Luật Ban hành VBQPPL 2015.
    Kiểm tra thứ tự ưu tiên áp dụng luật và tính toán điều kiện số cứng.
    """
    
    # Hierarchy level: Higher number = Higher legal authority
    HIERARCHY = {
        "Hiến pháp": 100,
        "Luật": 90,
        "Nghị quyết Quốc hội": 85,
        "Nghị định": 70,
        "Quyết định Thủ tướng": 60,
        "Thông tư": 50,
        "Nghị quyết HĐND Tỉnh": 40,
        "Quyết định UBND Tỉnh": 30
    }

    def resolve_legal_conflict(self, doc_a: Dict[str, Any], doc_b: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phân xử mâu thuẫn giữa 2 văn bản theo Điều 156 Luật BHVBQPPL 2015.
        """
        rank_a = self.HIERARCHY.get(doc_a.get("type", "Quyết định UBND Tỉnh"), 30)
        rank_b = self.HIERARCHY.get(doc_b.get("type", "Quyết định UBND Tỉnh"), 30)

        # Rule 1: Legal Hierarchy Priority
        if rank_a != rank_b:
            winner = doc_a if rank_a > rank_b else doc_b
            loser = doc_b if rank_a > rank_b else doc_a
            return {
                "winner": winner["name"],
                "reason": f"Theo Khoản 2 Điều 156 Luật BHVBQPPL, văn bản {winner['name']} có hiệu lực pháp lý cao hơn văn bản {loser['name']}.",
                "applied_rule": "Ưu tiên Văn bản có Hiệu lực Pháp lý Cao hơn"
            }
            
        # Rule 2: Temporal Priority (Same Hierarchy Rank)
        year_a = doc_a.get("year", 2020)
        year_b = doc_b.get("year", 2020)
        if year_a != year_b:
            winner = doc_a if year_a > year_b else doc_b
            loser = doc_b if year_a > year_b else doc_a
            return {
                "winner": winner["name"],
                "reason": f"Theo Khoản 3 Điều 156 Luật BHVBQPPL, cùng cấp ban hành thì văn bản {winner['name']} (năm {winner.get('year')}) được ban hành sau sẽ ưu tiên áp dụng.",
                "applied_rule": "Ưu tiên Văn bản Ban hành Sau"
            }

        return {
            "winner": "Cần Ban Pháp chế xem xét",
            "reason": "Hai văn bản cùng cấp thẩm quyền và ban hành cùng thời điểm.",
            "applied_rule": "Trình thẩm định Ban Pháp chế"
        }

    def check_noxh_profit_limit(self, profit_margin: float) -> Dict[str, Any]:
        """Kiểm tra điều kiện cứng lợi nhuận định mức NOXH (Tối đa 10%)."""
        if profit_margin <= 10.0:
            return {"status": "PASS", "msg": f"Lợi nhuận {profit_margin}% nằm trong khung hợp lệ theo Luật Nhà ở 2023 (Tối đa 10%)."}
        else:
            return {"status": "FAIL", "msg": f"Lợi nhuận {profit_margin}% vượt mức trần 10% theo quy định pháp luật NOXH."}

if __name__ == "__main__":
    engine = LegalRulesEngine()
    test_res = engine.resolve_legal_conflict(
        {"name": "Luật Đất đai 2024", "type": "Luật", "year": 2024},
        {"name": "Quyết định 12/UBND Tỉnh", "type": "Quyết định UBND Tỉnh", "year": 2023}
    )
    print("Conflict Resolution Result:")
    print("Winner:", test_res["winner"])
    print("Reason:", test_res["reason"])
