import subprocess
import sys

def pull_model():
    model_name = "qwen3:14b"
    print(f"[+] Đang tiến hành kéo mô hình '{model_name}' từ Ollama...")
    try:
        cmd = ["ollama", "pull", model_name]
        result = subprocess.run(cmd, check=True)
        print(f"[✅] Kéo thành công mô hình {model_name}!")
    except Exception as e:
        print(f"[⚠️] Lỗi khi kéo mô hình {model_name}: {e}")
        print("Bạn có thể mở PowerShell/CMD và gõ lệnh sau để tải về thủ công:")
        print(f"    ollama pull {model_name}")

if __name__ == "__main__":
    pull_model()
