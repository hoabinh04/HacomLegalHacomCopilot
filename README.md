# 🏛️ HACOM LEGAL COPILOT — HỆ THỐNG TRA CỨU PHÁP LÝ & CẢNH BÁO TÁC ĐỘNG DỰ ÁN
> **Tập đoàn HACOM Holdings** | Enterprise Legal AI Copilot (RAG & Knowledge Graph)

---

## ⚡ HƯỚNG DẪN KHỞI ĐỘNG NHANH TRONG 3 BƯỚC (QUICK START)

Dành cho người mới hoặc nhân sự chuyển giao dự án, thực hiện tuần tự 3 bước sau:

### 🔹 BƯỚC 1: Cài đặt môi trường & Thư viện
Mở **Terminal / PowerShell** tại thư mục dự án:

```powershell
# 1. Di chuyển vào thư mục dự án
cd C:\KHMT\HacomHoldings\HacomLegalCopilot

# 2. Tạo và kích hoạt môi trường ảo Python (nếu chưa có)
python -m venv .venv
.\.venv\Scripts\activate

# 3. Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```
*(Nếu máy đã có sẵn môi trường Conda `HacomKTKT`, bạn có thể dùng trực tiếp: `C:\KHMT\HacomHolding\HacomKTKT\.conda-env\python.exe -m pip install -r requirements.txt`)*

---

### 🔹 BƯỚC 2: Mở kết nối SSH Tunnel tới Server GPU (Chạy ở 1 Terminal riêng)
Hệ thống sử dụng mô hình ngôn ngữ lớn **Qwen3:8b** đặt tại máy chủ GPU doanh nghiệp. Hãy mở một cửa sổ **PowerShell riêng** và chạy lệnh:

```powershell
ssh -N -L 50050:localhost:11434 k16khmt-binh@118.70.169.236
```
> 💡 *Nhập mật khẩu SSH của server khi được yêu cầu. Giữ nguyên cửa sổ này chạy ngầm trong suốt thời gian sử dụng.*

---

### 🔹 BƯỚC 3: Khởi chạy Máy chủ Web Dashboard

Bạn có thể chọn **1 trong 3 cách** sau để chạy:

#### 👉 Cách 3.1: Nhấp đúp chuột (1-Click) — Tiện lợi nhất
Nhấp đúp chuột vào file:
```
start_hacom_legal.bat
```

#### 👉 Cách 3.2: Chạy bằng lệnh PowerShell / CMD tiêu chuẩn
```powershell
cd C:\KHMT\HacomHoldings\HacomLegalCopilot
python app.py
```

#### 👉 Cách 3.3: Chạy chỉ định môi trường Conda nội bộ
```powershell
cd C:\KHMT\HacomHoldings\HacomLegalCopilot
$env:HACOM_LLM_URL="http://localhost:50050"
$env:HACOM_LEGAL_MODEL="qwen3:8b"
C:\KHMT\HacomHolding\HacomKTKT\.conda-env\python.exe app.py
```

---

## 🌐 ĐỊA CHỈ TRUY CẬP HỆ THỐNG

Khi màn hình Terminal xuất hiện thông báo:  
`INFO: Uvicorn running on http://127.0.0.1:8005 (Press CTRL+C to quit)`

Bạn mở trình duyệt web và truy cập:

| Thành phần | Địa chỉ (URL) | Chức năng |
| :--- | :--- | :--- |
| **Giao diện Dashboard chính** | [http://127.0.0.1:8005/](http://127.0.0.1:8005/) | Màn hình Tra cứu RAG, Cảnh báo tác động và Đồ thị tri thức |

---

## 📖 HƯỚNG DẪN KIỂM THỬ 3 CHỨC NĂNG CHÍNH

### 1. 🔍 Tab 1: Tra cứu Pháp lý RAG (Verified Legal RAG)
* **Cách dùng**: Chọn loại hình dự án (*KĐT, Nhà ở xã hội, Năng lượng tái tạo, BĐS nghỉ dưỡng, Cụm công nghiệp*) ➔ Nhấp vào các câu hỏi gợi ý nhanh hoặc tự nhập câu hỏi ➔ Bấm **"Tra cứu ngay"**.
* **Câu hỏi mẫu thử nghiệm**:
  * `💡 Định mức lợi nhuận dự án Nhà ở xã hội là bao nhiêu %?` (AI sẽ trích dẫn Điều 85 Luật Nhà ở 2023 - mức tối đa 10%).
  * `💡 Thủ tục bồi thường GPMB khi thu hồi đất quy định như thế nào?` (AI sẽ trích dẫn Luật Đất đai & NĐ 102/2024).
  * `💡 Cơ chế mua bán điện trực tiếp DPPA theo Nghị định 80/2024` (AI sẽ phân tích cơ chế cho dự án điện gió).

### 2. 🚨 Tab 2: Cảnh báo Tác động Văn bản Mới
* **Cách dùng**: Nhập số hiệu văn bản mới ban hành (*ví dụ: `71/2024/NĐ-CP` hoặc `102/2024/NĐ-CP`*) ➔ Bấm **"Phân tích tác động dự án"**.
* **Kết quả**: Hệ thống tự động so khớp ma trận 7 dự án trọng điểm của HACOM (*KĐT K1, KĐT K2, Hacom GalaCity, Điện gió Hòa Thắng, Bình Sơn Resort...*) để đưa ra mức độ rủi ro (🔴 Đỏ / 🟡 Vàng / 🔵 Xanh) và khuyến nghị hành động.

### 3. 🕸️ Tab 3: Đồ thị Tri thức & Xử lý Xung đột Pháp lý
* **Cách dùng**: Nhấp vào tab **"Đồ thị tri thức"**.
* **Kết quả**: Xem 16 Nodes (Văn bản), 10 Edges (Quan hệ `AMENDS`, `GUIDES`, `CONFLICT_WITH`) và các thẻ gợi ý văn bản ưu tiên áp dụng theo **Điều 156 Luật Ban hành VBQPPL 2015**.

---

## ⚙️ CẤU HÌNH TÙY CHỌN (FILE `.env`)

Hệ thống tự động đọc các cấu hình từ file `.env` (hoặc biến môi trường hệ thống):

```env
HACOM_LLM_URL=http://localhost:50050       # Địa chỉ máy chủ LLM Ollama qua SSH Tunnel
HACOM_LEGAL_MODEL=qwen3:8b                 # Mô hình AI phục vụ (qwen3:8b hoặc qwen3:14b)
HACOM_LLM_TIMEOUT=120                      # Thời gian chờ tối đa (giây)
```

---

## 📁 CẤU TRÚC MÃ NGUỒN DỰ ÁN

```
HacomLegalCopilot/
├── app.py                         # File khởi động chính máy chủ FastAPI + Uvicorn
├── app_api.py                     # Định nghĩa RESTful API và giao diện Web HTML/CSS/JS
├── verified_rag.py                # Bộ máy Tra cứu RAG 4 lớp có kiểm chứng & chống ảo giác
├── alert_engine.py                # Động cơ đánh giá tác động văn bản mới lên các dự án HACOM
├── knowledge_graph.py             # Quản trị Đồ thị Tri thức pháp lý (Nodes, Edges, Conflicts)
├── vector_store.py                # Kho dữ liệu Vector & Tìm kiếm lai thông minh (Smart Hybrid Search)
├── pdf_parser.py                  # Module bóc tách cấu trúc Điều/Khoản từ 45 tệp PDF luật
├── config.py                      # Quản lý đường dẫn và cấu hình toàn cục
├── requirements.txt               # Danh sách thư viện Python phụ thuộc
├── start_hacom_legal.bat          # Kịch bản khởi động 1-Click trên Windows
├── README.md                      # Tài liệu hướng dẫn sử dụng và chuyển giao dự án
└── data/
    ├── legal_knowledge_graph.json # Dữ liệu đồ thị 16 Nodes, 10 Edges, 4 Xung đột pháp lý
    └── legal_vector_store/        # Cơ sở dữ liệu 1,145 Chunks đã được lập chỉ mục
```

---
*© 2026 Tập đoàn HACOM Holdings. Tài liệu phục vụ nội bộ Ban Pháp chế và Bộ phận Công nghệ.*
