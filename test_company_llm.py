import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8')

# Đọc .env
env_file = Path(__file__).resolve().parent / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

import json
import urllib.request
import urllib.error

def test_hacom_llm():
    url = os.getenv("HACOM_LLM_URL", "https://ai.hacomholdings.com.vn/api/llm/v1")
    key = os.getenv("HACOM_LLM_KEY", "")
    model = os.getenv("HACOM_LEGAL_MODEL", "Qwen/Qwen3.8-27B-FP8")

    print("=" * 70)
    print("KIEM TRA KET NOI CONG LLM HACOM (API_LLM_HACOM.md)")
    print("=" * 70)
    print(f"Endpoint: {url}")
    print(f"Model:    {model}")
    print(f"API Key:  {key[:10]}...{key[-6:]}" if key else "CHUA CO KEY")
    print("-" * 70)

    # 1. Phép thử 1: GET /models
    print("[1/2] Kiem tra ket noi va tinh hop le cua Key (GET /models)...")
    try:
        req = urllib.request.Request(
            f"{url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {key}"} if key else {}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  [OK] Ket noi thanh cong (HTTP 200)! Danh sach Model: {data}")
    except urllib.error.HTTPError as he:
        print(f"  [!] HTTP Error {he.code}: {he.reason}")
    except Exception as e:
        print(f"  [!] Network Error: {e}")

    # 2. Phép thử 2: POST /chat/completions
    if key:
        print("\n[2/2] Gui thu nghiem cau hoi phap ly (POST /chat/completions)...")
        try:
            payload = json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": "Ban la tro ly phap ly cao cap cua Tap doan HACOM Holdings. Tra loi ngan gon."},
                    {"role": "user", "content": "Xac nhan he thong HACOM Legal Copilot da ket noi thanh cong voi mo hinh Qwen3.8-27B."}
                ],
                "max_tokens": 128,
                "temperature": 0.15
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{url.rstrip('/')}/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {key}"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    ans = choices[0].get("message", {}).get("content", "")
                    print(f"  [OK] Phan hoi truc tiep tu mo hinh {model}:")
                    print(f"  '{ans.strip()}'")
        except urllib.error.HTTPError as he:
            print(f"  [!] HTTP Error {he.code}: {he.reason}")
        except Exception as e:
            print(f"  [!] Error: {e}")

if __name__ == "__main__":
    test_hacom_llm()
