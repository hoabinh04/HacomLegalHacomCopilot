import sys
import os
import uvicorn
import urllib.request
import json
from pathlib import Path

# Thêm thư mục hiện tại vào Python Path để chạy độc lập hoàn toàn
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import DEFAULT_LLM_MODEL, OLLAMA_HOST, LUAT_ND_DIR, VECTOR_DB_PATH
from vector_store import LegalVectorStore
from knowledge_graph import LegalKnowledgeGraph
from pdf_parser import LegalPDFParser

def check_and_index_data():
    """Kiểm tra và tự động lập chỉ mục CSDL nếu chưa có."""
    vector_store = LegalVectorStore()
    if not vector_store.chunks:
        print("[+] Kho dữ liệu Vector chưa có chỉ mục. Đang tiến hành nạp dữ liệu từ Luat_NĐ...")
        pdf_files = list(LUAT_ND_DIR.glob("*.pdf"))
        if pdf_files:
            parser = LegalPDFParser()
            all_chunks = []
            for pdf in pdf_files:
                chunks = parser.parse_legal_chunks(pdf)
                all_chunks.extend(chunks)
            vector_store.add_chunks(all_chunks)
            print(f"[+] Đã đánh chỉ mục thành công {len(all_chunks)} đoạn dữ liệu pháp lý.")
        else:
            print("[!] Không tìm thấy tệp PDF trong thư mục Luat_NĐ.")
    else:
        print(f"[+] Kho dữ liệu đã sẵn sàng: {len(vector_store.chunks)} chunks được đánh chỉ mục.")

def check_ollama_status():
    """Kiểm tra trạng thái Ollama và mô hình qwen3:14b."""
    print(f"[+] Đang kết nối tới Ollama LLM tại: {OLLAMA_HOST}")
    print(f"[+] Mô hình AI chỉ định: {DEFAULT_LLM_MODEL}")
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            print(f"[+] Danh sách mô hình hiện có trong Ollama: {models}")
            if DEFAULT_LLM_MODEL in models or any("qwen" in m.lower() for m in models):
                print(f"[✅] Mô hình '{DEFAULT_LLM_MODEL}' đã sẵn sàng phục vụ.")
            else:
                print(f"[⚠️] Chưa tìm thấy mô hình '{DEFAULT_LLM_MODEL}' trong Ollama. Hệ thống sẽ tự chọn mô hình sẵn có hoặc kéo về với lệnh 'ollama pull {DEFAULT_LLM_MODEL}'.")
    except Exception as e:
        print(f"[⚠️] Không thể kết nối tới Ollama Service ({e}). Hệ thống sẽ chạy ở chế độ Tra cứu Kiểm chứng Rule-based Fallback.")

def main():
    print("=" * 65)
    print("🚀 KHỞI ĐỘNG HỆ THỐNG HACOM LEGAL COPILOT (ĐỘC LẬP)")
    print("   Tập đoàn HACOM Holdings - Tra cứu Pháp lý & Cảnh báo Tác động")
    print("=" * 65)

    # 1. Tự động kiểm tra & nạp CSDL
    check_and_index_data()

    # 2. Kiểm tra Ollama LLM & qwen3:14b
    check_ollama_status()

    # 3. Khởi chạy FastAPI Web Server & Enterprise Dashboard
    print("-" * 65)
    print("🌐 Đang khởi chạy Server Web Dashboard tại: http://127.0.0.1:8005/")
    print("=" * 65)

    uvicorn.run("app_api:app", host="127.0.0.1", port=8005, reload=False)

if __name__ == "__main__":
    main()
