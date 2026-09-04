import sys
import time
from pathlib import Path

from config import LUAT_ND_DIR
from pdf_parser import LegalPDFParser
from vector_store import LegalVectorStore
from knowledge_graph import LegalKnowledgeGraph

def main():
    print("=" * 60)
    print("🚀 KHỞI ĐỘNG TIẾN TRÌNH NẠP KHO DỮ LIỆU HACOM LEGAL COPILOT")
    print("=" * 60)
    
    if not LUAT_ND_DIR.exists():
        print(f"❌ Lỗi: Thư mục kho luật không tồn tại: {LUAT_ND_DIR}")
        return

    pdf_files = sorted(list(LUAT_ND_DIR.glob("*.pdf")))
    print(f"📁 Tìm thấy tổng cộng: {len(pdf_files)} tệp PDF văn bản pháp luật.")
    
    parser = LegalPDFParser()
    vector_store = LegalVectorStore()
    kg = LegalKnowledgeGraph()

    total_chunks = 0
    start_time = time.time()

    for idx, pdf in enumerate(pdf_files, 1):
        print(f"[{idx:02d}/{len(pdf_files):02d}] Đang bóc tách & đánh chỉ mục: {pdf.name[:45]}...")
        try:
            chunks = parser.parse_legal_chunks(pdf)
            if chunks:
                vector_store.add_chunks(chunks)
                total_chunks += len(chunks)
        except Exception as e:
            print(f"  ⚠️ Lỗi khi xử lý {pdf.name}: {e}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("🎉 HOÀN THÀNH ĐÁNH CHỈ MỤC KHO DỮ LIỆU PHÁP LÝ HACOM LEGAL COPILOT!")
    print(f"- Tổng số văn bản đã xử lý: {len(pdf_files)} file PDF")
    print(f"- Tổng số đoạn Điều/Khoản đã nạp vào Vector Store: {total_chunks} chunks")
    print(f"- Thời gian thực thi: {elapsed:.2f} giây")
    print("=" * 60)

if __name__ == "__main__":
    main()
