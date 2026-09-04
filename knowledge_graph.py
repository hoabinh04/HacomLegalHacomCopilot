import json
from pathlib import Path
from typing import Dict, Any, List
from config import GRAPH_DB_PATH

class LegalKnowledgeGraph:
    """
    Đồ thị Tri thức Pháp lý (Legal Knowledge Graph Engine).
    Quản lý các mối quan hệ (GUIDES, AMENDS, CONFLICT_WITH) và phân xử xung đột theo Điều 156.
    """
    
    def __init__(self, db_path: Path = GRAPH_DB_PATH):
        self.db_path = db_path
        self.nodes: Dict[str, Any] = {}
        self.edges: List[Dict[str, Any]] = []
        self.load_graph()

    def load_graph(self):
        if self.db_path.exists():
            try:
                data = json.loads(self.db_path.read_text(encoding="utf-8"))
                self.nodes = data.get("nodes", {})
                self.edges = data.get("edges", [])
                self._ensure_conflict_edges()
            except Exception:
                self._initialize_default_graph()
        else:
            self._initialize_default_graph()
            self.save_graph()

    def _ensure_conflict_edges(self):
        existing_conflicts = [e for e in self.edges if e.get("relation") == "CONFLICT_WITH"]
        if not existing_conflicts:
            default_conflicts = [
                {
                    "source": "102/2024/NĐ-CP",
                    "target": "30/2020/NĐ-CP",
                    "relation": "CONFLICT_WITH",
                    "desc": "Mâu thuẫn về thời hạn niêm yết thông báo thu hồi đất và thời gian lưu trữ văn bản bồi thường",
                    "recommended_doc": "102/2024/NĐ-CP (Nghị định Chi tiết thi hành Luật Đất đai 2024)",
                    "legal_basis": "Theo Điều 156 Khoản 2 Luật BHVBQPPL 2015, Nghị định 102/2024/NĐ-CP là văn bản quy định chuyên ngành đất đai được ưu tiên áp dụng cho khâu thu hồi và bồi thường GPMB.",
                    "hacom_recommendation": "Áp dụng Nghị định 102/2024/NĐ-CP cho quy trình GPMB dự án KĐT Đông Bắc K1, KĐT Bình Sơn K2 và Dốc Đá Phú Tài."
                },
                {
                    "source": "100/2024/NĐ-CP",
                    "target": "96/2024/NĐ-CP",
                    "relation": "CONFLICT_WITH",
                    "desc": "Mâu thuẫn về điều kiện nghiệm thu móng và xác nhận miễn tiền sử dụng đất trước khi thông báo mở bán",
                    "recommended_doc": "100/2024/NĐ-CP (Nghị định Phát triển và Quản lý Nhà ở Xã hội)",
                    "legal_basis": "Theo Điều 156 Khoản 3 Luật BHVBQPPL 2015, văn bản chuyên biệt quy định cho Nhà ở xã hội được ưu tiên áp dụng so với quy định chung về BĐS thương mại.",
                    "hacom_recommendation": "Áp dụng Nghị định 100/2024/NĐ-CP và NĐ 136/2026/NĐ-CP cho hồ sơ điều kiện mở bán Nhà ở xã hội Hacom GalaCity."
                },
                {
                    "source": "80/2024/NĐ-CP",
                    "target": "19/2023/TT-BCT",
                    "relation": "CONFLICT_WITH",
                    "desc": "Khác biệt về trần giá giao dịch điện trực tiếp ngoài hợp đồng PPA chuẩn của EVN",
                    "recommended_doc": "80/2024/NĐ-CP (Nghị định quy định Cơ chế Mua bán điện trực tiếp DPPA)",
                    "legal_basis": "Theo Điều 156 Khoản 1 Luật BHVBQPPL 2015, Nghị định (cấp Chính phủ) có hiệu lực pháp lý cao hơn Thông tư (cấp Bộ).",
                    "hacom_recommendation": "Ưu tiên áp dụng Nghị định 80/2024/NĐ-CP để đàm phán hợp đồng mua bán điện DPPA trực tiếp cho dự án Điện gió Hòa Thắng 1.2."
                },
                {
                    "source": "71/2024/NĐ-CP",
                    "target": "88/2024/NĐ-CP",
                    "relation": "CONFLICT_WITH",
                    "desc": "Khác biệt về thời điểm chốt giá đất cụ thể để tính toán tiền đền bù GPMB",
                    "recommended_doc": "71/2024/NĐ-CP (Cho phương pháp định giá) & 88/2024/NĐ-CP (Cho trình tự niêm yết)",
                    "legal_basis": "Áp dụng kết hợp theo nguyên tắc chuyên ngành: NĐ 71 cho thuật toán thặng dư/so sánh và NĐ 88 cho thời hạn công khai phương án bồi thường.",
                    "hacom_recommendation": "Ban Pháp chế dùng NĐ 71 để thẩm định đơn giá và NĐ 88 để thực hiện niêm yết GPMB."
                }
            ]
            self.edges.extend(default_conflicts)
            self.save_graph()

    def _initialize_default_graph(self):
        self.nodes = {
            "31/2024/QH15": {"title": "Luật Đất đai 2024", "status": "Active"},
            "102/2024/NĐ-CP": {"title": "Nghị định 102/2024/NĐ-CP Chi tiết Luật Đất đai", "status": "Active"},
            "71/2024/NĐ-CP": {"title": "Nghị định 71/2024/NĐ-CP Định giá đất", "status": "Active"},
            "88/2024/NĐ-CP": {"title": "Nghị định 88/2024/NĐ-CP Bồi thường GPMB", "status": "Active"},
            "27/2023/QH15": {"title": "Luật Nhà ở 2023", "status": "Active"},
            "95/2024/NĐ-CP": {"title": "Nghị định 95/2024/NĐ-CP Chi tiết Luật Nhà ở", "status": "Active"},
            "100/2024/NĐ-CP": {"title": "Nghị định 100/2024/NĐ-CP Phát triển NOXH", "status": "Active"},
            "136/2026/NĐ-CP": {"title": "Nghị định 136/2026/NĐ-CP Sửa đổi NĐ 100/2024 về NOXH", "status": "Active"},
            "29/2023/QH15": {"title": "Luật Kinh doanh Bất động sản 2023", "status": "Active"},
            "96/2024/NĐ-CP": {"title": "Nghị định 96/2024/NĐ-CP Chi tiết Luật KDBĐS", "status": "Active"},
            "22/2023/QH15": {"title": "Luật Đấu thầu 2023", "status": "Active"},
            "23/2024/NĐ-CP": {"title": "Nghị định 23/2024/NĐ-CP Đấu thầu nhà đầu tư", "status": "Active"},
            "80/2024/NĐ-CP": {"title": "Nghị định 80/2024/NĐ-CP Cơ chế DPPA điện", "status": "Active"},
            "19/2023/TT-BCT": {"title": "Thông tư 19/2023/TT-BCT Khung giá phát điện", "status": "Active"},
            "135/2025/QH15": {"title": "Luật Xây dựng 2025", "status": "Active"},
            "175/2024/NĐ-CP": {"title": "Nghị định 175/2024/NĐ-CP Chi tiết Luật Xây dựng", "status": "Active"},
            "50/2024/NĐ-CP": {"title": "Nghị định 50/2024/NĐ-CP về PCCC", "status": "Active"}
        }
        
        self.edges = [
            {"source": "102/2024/NĐ-CP", "target": "31/2024/QH15", "relation": "GUIDES", "desc": "Hướng dẫn thi hành"},
            {"source": "71/2024/NĐ-CP", "target": "31/2024/QH15", "relation": "GUIDES", "desc": "Hướng dẫn định giá đất"},
            {"source": "88/2024/NĐ-CP", "target": "31/2024/QH15", "relation": "GUIDES", "desc": "Hướng dẫn Bồi thường GPMB"},
            {"source": "136/2026/NĐ-CP", "target": "100/2024/NĐ-CP", "relation": "AMENDS", "desc": "Sửa đổi bổ sung NĐ 100/2024 về NOXH"},
            {"source": "96/2024/NĐ-CP", "target": "29/2023/QH15", "relation": "GUIDES", "desc": "Hướng dẫn Luật KDBĐS 2023"},
            {"source": "23/2024/NĐ-CP", "target": "22/2023/QH15", "relation": "GUIDES", "desc": "Hướng dẫn đấu thầu nhà đầu tư sử dụng đất"}
        ]
        self._ensure_conflict_edges()

    def save_graph(self):
        data = {"nodes": self.nodes, "edges": self.edges}
        self.db_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_document_node(self, doc_id: str, title: str, doc_type: str = "Nghị định", field: str = "Đất đai") -> bool:
        """Thêm văn bản luật mới vào Đồ thị Tri thức và lưu trữ vĩnh viễn."""
        self.nodes[doc_id] = {
            "title": title,
            "type": doc_type,
            "field": field,
            "status": "Active"
        }
        self.save_graph()
        return True

    def get_related_laws(self, doc_number: str) -> List[Dict[str, Any]]:
        results = []
        for edge in self.edges:
            if edge.get("source") == doc_number or edge.get("target") == doc_number:
                results.append(edge)
        return results

    def get_conflicts(self) -> List[Dict[str, Any]]:
        """Lấy danh sách các trường hợp Xung đột Pháp lý và Gợi ý xử lý."""
        return [e for e in self.edges if e.get("relation") == "CONFLICT_WITH"]

if __name__ == "__main__":
    kg = LegalKnowledgeGraph()
    print(f"Legal Knowledge Graph initialized with {len(kg.nodes)} nodes and {len(kg.edges)} relations.")


    def get_precedences(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ danh sách các quan hệ phân xử phủ quyết / sửa đổi theo Điều 156."""
        try:
            from legal_precedence_engine import LegalPrecedenceEngine
            engine = LegalPrecedenceEngine()
            return engine.get_all_precedence_rules()
        except Exception:
            return []
