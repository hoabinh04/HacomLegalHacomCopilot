import sys
import os
import uvicorn
import urllib.request
import json
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
except Exception:
    pass

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import (
    DEFAULT_LLM_MODEL, HACOM_LLM_URL, HACOM_LLM_KEY, 
    LUAT_ND_DIR, VECTOR_DB_PATH
)
from vector_store import LegalVectorStore
from knowledge_graph import LegalKnowledgeGraph
from pdf_parser import LegalPDFParser

def check_and_index_data():
    """Kiểm tra và tự động nạp CSDL nếu chưa có."""
    vector_store = LegalVectorStore()
    if not vector_store.chunks:
        print("[+] Kho dữ liệu Vector chưa có chỉ mục. Đang kiểm tra thư mục Luat_NĐ...")
        pdf_files = list(LUAT_ND_DIR.glob("*.pdf")) if LUAT_ND_DIR.exists() else []
        if pdf_files:
            parser = LegalPDFParser()
            all_chunks = []
            for pdf in pdf_files:
                chunks = parser.parse_legal_chunks(pdf)
                all_chunks.extend(chunks)
            vector_store.add_chunks(all_chunks)
            print(f"[+] Đã đánh chỉ mục thành công {len(all_chunks)} đoạn dữ liệu pháp lý.")
        else:
            print("[!] Không tìm thấy tệp PDF để lập chỉ mục mới.")
    else:
        print(f"[+] Kho dữ liệu đã sẵn sàng: {len(vector_store.chunks)} chunks được lập chỉ mục.")

def check_llm_status():
    """Kiểm tra kết nối tới Model AI (HACOM LLM Gateway hoặc Ollama)."""
    print(f"[+] Đang kết nối tới Cổng AI: {HACOM_LLM_URL}")
    print(f"[+] Mô hình AI chỉ định: {DEFAULT_LLM_MODEL}")
    
    # 1. Nếu dùng Cổng AI HACOM (OpenAI-compatible)
    if "hacomholdings" in HACOM_LLM_URL or HACOM_LLM_KEY:
        try:
            req = urllib.request.Request(
                f"{HACOM_LLM_URL.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {HACOM_LLM_KEY}"} if HACOM_LLM_KEY else {}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("id") for m in data.get("data", [])]
                print(f"[✅] Kết nối thành công Cổng AI HACOM! Danh sách Model: {models}")
                print(f"[✅] Mô hình '{DEFAULT_LLM_MODEL}' đã sẵn sàng phục vụ.")
                return
        except Exception as e:
            print(f"[⚠️] Không thể xác thực Cổng AI HACOM ({e}). Sẽ sử dụng Fallback nếu cần.")
            return

    # 2. Nếu dùng Ollama Local
    try:
        req = urllib.request.Request(f"{HACOM_LLM_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            print(f"[+] Danh sách mô hình hiện có trong Ollama: {models}")
            if DEFAULT_LLM_MODEL in models or any("qwen" in m.lower() for m in models):
                print(f"[✅] Mô hình '{DEFAULT_LLM_MODEL}' đã sẵn sàng phục vụ.")
            else:
                print(f"[⚠️] Chưa tìm thấy mô hình '{DEFAULT_LLM_MODEL}' trong Ollama.")
    except Exception as e:
        print(f"[⚠️] Không thể kết nối tới Ollama ({e}).")

def main():
    print("=" * 65)
    print("🚀 KHỞI ĐỘNG HỆ THỐNG HACOM LEGAL COPILOT (ĐỘC LẬP)")
    print("   Tập đoàn HACOM Holdings - Tra cứu Pháp lý & Cảnh báo Tác động")
    print(f"   AI Model: {DEFAULT_LLM_MODEL}")
    print("=" * 65)

    # 1. Kiểm tra CSDL
    check_and_index_data()

    # 2. Kiểm tra Model AI
    check_llm_status()

    # 3. Khởi chạy FastAPI Web Server (Lắng nghe 0.0.0.0 toàn mạng)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8005"))
    print("-" * 65)
    print(f"🌐 Đang khởi chạy Server Web Dashboard tại: http://{host}:{port}/")
    print("=" * 65)

    uvicorn.run("app_api:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
