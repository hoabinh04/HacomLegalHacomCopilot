import json
import re
from pathlib import Path
from typing import List, Dict, Any
from config import VECTOR_DB_PATH

STOP_WORDS = {
    'là', 'của', 'và', 'các', 'trong', 'cho', 'với', 'được', 'khi', 'bao', 'nhiêu', 
    'gì', 'như', 'thế', 'nào', 'ra', 'sao', 'đến', 'tại', 'về', 'do', 'đã', 'đang', 
    'sẽ', 'thì', 'theo', 'những', 'đó', 'này', 'từ', 'có', 'phải', 'dự', 'án', 'quy', 'định',
    'bị', 'cho', 'hay', 'ở', 'tại', 'như', 'cùng', 'sau'
}

PROJECT_KEYWORDS = {
    "NOXH": ["nhà ở xã hội", "nhà ở", "luat nha o", "100/2024", "27-2023"],
    "KĐT": ["đất đai", "thu hồi đất", "bồi thường", "gpmb", "giá đất", "bảng giá", "102/2024", "71/2024", "31-2024"],
    "NLTT": ["điện lực", "năng lượng", "điện gió", "dppa", "80/2024", "153-vbhn"],
    "ND": ["nghỉ dưỡng", "du lịch", "condotel", "villas", "kinh doanh bds", "29-2023"],
    "CCN": ["cụm công nghiệp", "khu công nghiệp", "nước thải", "đtm", "143-2025", "32/2024"],
    "DTT": ["đấu thầu", "lựa chọn nhà đầu tư", "sử dụng đất", "115/2024", "đấu giá"],
    "TC": ["giá đất", "tiền sử dụng đất", "thặng dư", "71/2024", "nghĩa vụ tài chính", "thuế"]
}


# TỪ ĐIỂN ĐỒNG NGHĨA & CHUYỂN HÓA VĂN PHONG TỰ DO SANG THUẬT NGỮ PHÁP LÝ CHUẨN
CONVERSATIONAL_SYNONYMS = {
    "đền bù": ["bồi thường", "hỗ trợ", "tái định cư", "gpmb", "nghị định 88/2024", "88/2024/nđ-cp"],
    "đền tiền": ["bồi thường bằng tiền", "tiền bồi thường", "giá đất bồi thường"],
    "sổ đỏ": ["giấy chứng nhận", "giấy chứng nhận quyền sử dụng đất", "cấp sổ đỏ", "điều 137", "điều 138", "thông tư 10/2024"],
    "sổ hồng": ["giấy chứng nhận quyền sở hữu nhà ở", "căn hộ", "condotel", "sổ hồng"],
    "không có giấy tờ": ["đất không có giấy tờ", "chưa được cấp giấy chứng nhận", "điều 138 luật đất đai"],
    "lời bao nhiêu": ["lợi nhuận định mức", "định mức 10%", "tối đa 10%", "nghị định 100/2024"],
    "lãi bao nhiêu": ["lợi nhuận định mức", "định mức lợi nhuận", "10%"],
    "lợi nhuận": ["lợi nhuận định mức", "định mức lợi nhuận", "tối đa 10%", "chi phí hợp lý"],
    "bán điện cho dân": ["dppa", "mua bán điện trực tiếp", "nghị định 80/2024", "khách hàng sử dụng điện lớn"],
    "không qua evn": ["mua bán điện trực tiếp", "dppa", "đơn vị phát điện năng lượng tái tạo", "80/2024"],
    "lấy đất": ["thu hồi đất", "bồi thường thu hồi đất", "nghị định 102/2024", "điều 79", "điều 80"],
    "giải tỏa": ["giải phóng mặt bằng", "bồi thường gpmb", "thu hồi đất", "tái định cư"],
    "đất bỏ hoang": ["thu hồi đất do vi phạm", "chậm tiến độ 24 tháng", "điều 81 luật đất đai"],
    "chậm tiến độ": ["gia hạn tiến độ", "chậm đưa đất vào sử dụng", "24 tháng", "điều 81"],
    "thuế đất": ["tiền sử dụng đất", "tiền thuê đất", "nghị định 103/2024", "bảng giá đất"],
    "định giá": ["phương pháp thặng dư", "4 phương pháp định giá đất", "nghị định 71/2024", "71/2024"],
    "được mua nhà ở xã hội": ["đối tượng hưởng chính sách", "điều kiện thu nhập", "điều kiện nhà ở", "điều 76", "điều 78"],
    "thu nhập bao nhiêu": ["điều kiện thu nhập", "15 triệu", "30 triệu", "thu nhập chịu thuế", "nghị định 100/2024"],
    "cháy nổ": ["pccc", "phòng cháy chữa cháy", "qcvn 06:2022", "nghị định 50/2024"],
    "chọn nhà đầu tư": ["đấu thầu", "lựa chọn nhà đầu tư", "tiêu chuẩn m3", "nghị định 115/2024", "115/2024"]
}

CRITICAL_TERMS = [
    "bảng giá đất", "bảng giá", "khung giá đất", "định giá đất", "nguyên tắc định giá",
    "lợi nhuận định mức", "định mức lợi nhuận", "lợi nhuận", "định mức", "giá bán",
    "dppa", "điện gió", "năng lượng tái tạo", "bồi thường gpmb", "bồi thường", "tái định cư",
    "nước thải", "condotel", "villas", "sổ hồng", "chuyển nhượng dự án",
    "thu hồi đất", "giá đất", "nhà ở xã hội", "cụm công nghiệp",
    "đấu thầu", "đấu giá", "lựa chọn nhà đầu tư", "nhà đầu tư", "phương pháp thặng dư", 
    "tiền sử dụng đất", "tiền thuê đất", "miễn tiền sử dụng đất", "đtm", "đánh giá tác động môi trường",
    "ký quỹ", "bảo đảm thực hiện dự án"
]

class LegalVectorStore:
    """
    Vector Store & Hybrid Search Engine cho Văn bản Pháp luật HACOM.
    Hỗ trợ tìm kiếm thông minh kết hợp Trùng khớp Cụm từ chuyên môn và 7 Phân loại Dự án.
    """
    
    def __init__(self, store_dir: Path = VECTOR_DB_PATH):
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.store_dir / "legal_chunks_index.json"
        self.chunks: List[Dict[str, Any]] = []
        self.load_store()

    def load_store(self):
        if self.index_file.exists():
            try:
                self.chunks = json.loads(self.index_file.read_text(encoding="utf-8"))
            except Exception:
                self.chunks = []

    def save_store(self):
        self.index_file.write_text(json.dumps(self.chunks, ensure_ascii=False, indent=2), encoding="utf-8")



    def update_document_metadata(self, old_identifier: str, new_doc_number: str, new_doc_name: str, new_field: str, new_issue_date: str = "", new_effective_date: str = "") -> int:
        """Cập nhật Số hiệu, Tên văn bản, Lĩnh vực, Ngày ban hành & Ngày hiệu lực cho toàn bộ chunks."""
        if not old_identifier:
            return 0
        old_clean = str(old_identifier).strip().lower()
        updated_count = 0
        for c in self.chunks:
            if (c.get("doc_name", "").strip().lower() == old_clean or 
                c.get("source_file", "").strip().lower() == old_clean or 
                c.get("doc_number", "").strip().lower() == old_clean):
                if new_doc_number:
                    c["doc_number"] = new_doc_number.strip()
                if new_doc_name:
                    c["doc_name"] = new_doc_name.strip()
                if new_field:
                    c["field"] = new_field.strip()
                if new_issue_date:
                    c["issue_date"] = new_issue_date.strip()
                if new_effective_date:
                    c["effective_date"] = new_effective_date.strip()
                updated_count += 1
        if updated_count > 0:
            self.save_store()
        return updated_count

    def delete_document(self, doc_identifier: str) -> int:
        """Xóa văn bản theo tên hoặc số hiệu và lưu lại chỉ mục."""
        if not doc_identifier:
            return 0
        doc_clean = str(doc_identifier).strip().lower()
        initial_count = len(self.chunks)
        self.chunks = [
            c for c in self.chunks
            if c.get("doc_name", "").strip().lower() != doc_clean
            and c.get("source_file", "").strip().lower() != doc_clean
            and c.get("doc_number", "").strip().lower() != doc_clean
        ]
        deleted_count = initial_count - len(self.chunks)
        if deleted_count > 0:
            self.save_store()
        return deleted_count

    def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        self.chunks.extend(new_chunks)
        self.save_store()

    def search(self, query: str, project_type: str = "Chung", top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Tìm kiếm lai thông minh kết hợp mở rộng ngữ nghĩa văn phong tự do (Semantic Synonym Expansion).
        """
        if not self.chunks:
            return []

        q_lower = query.lower()

        # TỰ ĐỘNG MỞ RỘNG TỪ ĐỒNG NGHĨA VĂN PHONG ĐỜI THƯỜNG SANG THUẬT NGỮ PHÁP LUẬT
        expanded_terms = []
        for conv_term, legal_synonyms in CONVERSATIONAL_SYNONYMS.items():
            if conv_term in q_lower:
                expanded_terms.extend(legal_synonyms)
        matched_critical = [t for t in CRITICAL_TERMS if t in q_lower]
        words = [w for w in re.findall(r'\w+', q_lower) if w not in STOP_WORDS and len(w) > 1]

        scored_results = []
        for chunk in self.chunks:
            content_lower = chunk.get("content", "").lower()
            doc_name_lower = chunk.get("doc_name", "").lower()
            doc_num_lower = chunk.get("doc_number", "").lower()
            article_lower = chunk.get("article", "").lower()
            
            score = 0.0

            # 1. Trọng số cực lớn cho thuật ngữ chuyên môn & Từ đồng nghĩa mở rộng
            for term in matched_critical + expanded_terms:
                if term in content_lower:
                    score += 300.0 + content_lower.count(term) * 50.0
                if term in doc_name_lower:
                    score += 150.0
                if term in article_lower:
                    score += 100.0

            # 2. Trọng số từ khóa có nghĩa
            for w in words:
                if w in content_lower:
                    score += content_lower.count(w) * 2.0
                if w in doc_name_lower:
                    score += 15.0
                if w in article_lower:
                    score += 25.0

            # 3. Phân loại theo 7 Nhóm Dự án cốt lõi HACOM
            if project_type in PROJECT_KEYWORDS:
                for kw in PROJECT_KEYWORDS[project_type]:
                    if kw in doc_name_lower or kw in doc_num_lower:
                        score += 40.0
                    elif kw in content_lower:
                        score += 10.0

            if score > 0:
                scored_results.append((score, chunk))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        if scored_results:
            return [item[1] for item in scored_results[:top_k]]
        
        # Fallback: Trả về 3 chunk đầu tiên nếu không có điểm nào
        return self.chunks[:top_k]

if __name__ == "__main__":
    store = LegalVectorStore()
    print("Vector Store loaded with", len(store.chunks), "legal chunks.")
