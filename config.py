import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
except Exception:
    pass
import os
from pathlib import Path

# Tự động nhận diện thư mục dự án trên mọi hệ điều hành (Windows / Linux Ubuntu)
LEGAL_COPILOT_DIR = Path(__file__).resolve().parent
BASE_DIR = LEGAL_COPILOT_DIR.parent
LUAT_ND_DIR = BASE_DIR / "Luat_NĐ"
DATA_DIR = LEGAL_COPILOT_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = DATA_DIR / "uploaded_laws"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Load .env file if exists
env_file = LEGAL_COPILOT_DIR / ".env"
if env_file.exists():
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()
    except Exception:
        pass

# Database Paths (Tương thích 100% đa nền tảng)
VECTOR_DB_PATH = DATA_DIR / "legal_vector_store"
GRAPH_DB_PATH = DATA_DIR / "legal_knowledge_graph.json"
RULES_DB_PATH = DATA_DIR / "legal_rules.json"

# ==============================================================================
# HACOM OFFICIAL LLM CONFIGURATION (Qwen3.8-27B-FP8 via HACOM Internal Gateway)
# ==============================================================================
HACOM_LLM_URL = os.getenv("HACOM_LLM_URL", "https://ai.hacomholdings.com.vn/api/llm/v1")
HACOM_LLM_KEY = os.getenv("HACOM_LLM_KEY", os.getenv("OPENAI_API_KEY", ""))
DEFAULT_LLM_MODEL = os.getenv("HACOM_LEGAL_MODEL", "Qwen/Qwen3.8-27B-FP8")
HACOM_LLM_TIMEOUT = int(os.getenv("HACOM_LLM_TIMEOUT", "180"))

# Backward compatibility aliases
OLLAMA_HOST = HACOM_LLM_URL

# Legal Document Types
DOC_TYPES = [
    "Luật",
    "Nghị định",
    "Thông tư",
    "Quyết định",
    "Văn bản Hợp nhất"
]

# HACOM 7 Core Legal & Project Types
PROJECT_TYPES = {
    "KĐT": "Khu đô thị & Bất động sản thương mại",
    "NOXH": "Nhà ở & Nhà ở xã hội",
    "NLTT": "Năng lượng tái tạo & Điện lực",
    "ND": "Bất động sản nghỉ dưỡng & Khách sạn",
    "CCN": "Cụm công nghiệp & Hạ tầng kỹ thuật",
    "DTT": "Đấu thầu & Lựa chọn nhà đầu tư dự án",
    "TC": "Tài chính đất đai & Định giá đất"
}

print(f"[+] HacomLegalCopilot Config Loaded.")
print(f"    Thư mục dự án: {LEGAL_COPILOT_DIR}")
print(f"    Vector Store Path: {VECTOR_DB_PATH}")
print(f"    HACOM Official LLM Gateway: {HACOM_LLM_URL} (Model: {DEFAULT_LLM_MODEL})")
