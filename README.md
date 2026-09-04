# ⚖️ HACOM LEGAL COPILOT — HỆ THỐNG TRỢ LÝ PHÁP LÝ & THẨM ĐỊNH DỰ ÁN AI
> **TẬP ĐOÀN HACOM HOLDINGS** | Enterprise Legal AI Copilot (RAG & Knowledge Graph)  
> **Model Core:** `Qwen/Qwen3.8-27B-FP8` (Hạ tầng Máy chủ AI Nội bộ Tập đoàn HACOM)

---

## 🌟 TỔNG QUAN HỆ THỐNG

**HACOM Legal Copilot** là nền tảng Trí tuệ Nhân tạo chuyên biệt phục vụ công tác tra cứu, thẩm định và đánh giá rủi ro pháp lý cho các dự án đầu tư trọng điểm của Tập đoàn HACOM Holdings (Khu đô thị, Nhà ở xã hội, Năng lượng tái tạo, Bất động sản nghỉ dưỡng, Cụm công nghiệp).

Hệ thống kết hợp **Kiến trúc RAG 4 lớp có kiểm chứng (Verified RAG)** với **Đồ thị Tri thức Pháp lý (Legal Knowledge Graph)** và kết nối trực tiếp với cụm máy chủ **AI nội bộ của HACOM Holdings**, đảm bảo:
* 🔒 **Bảo mật tuyệt đối**: Dữ liệu không gửi ra ngoài Internet; vận hành qua Cổng AI nội bộ của Tập đoàn.
* 🎯 **Chính xác & Trực diện**: 100% câu trả lời đều trích dẫn chính xác Điều, Khoản, Điểm và Văn bản quy phạm pháp luật áp dụng.
* ⚡ **Xử lý xung đột pháp luật**: Tự động xác định thứ bậc hiệu lực pháp lý theo **Điều 156 Luật Ban hành VBQPPL 2015**.

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY (QUICK START)

### 1️⃣ Cài đặt Môi trường & Thư viện

```bash
# Di chuyển vào thư mục dự án
cd HacomLegalCopilot

# Tạo và kích hoạt môi trường ảo
python -m venv .venv

# Trên Windows:
.\.venv\Scripts\activate

# Trên Linux/Ubuntu Server:
source .venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

---

### 2️⃣ Cấu hình Biến Môi trường (`.env`)

Tạo hoặc chỉnh sửa file `.env` tại thư mục gốc của dự án:

```ini
# ==============================================================================
# CỔNG AI NỘI BỘ TẬP ĐOÀN HACOM (Qwen3.8-27B-FP8)
# ==============================================================================
HACOM_LLM_URL=https://ai.hacomholdings.com.vn/api/llm/v1
HACOM_LLM_KEY=291dbde4a94cfd5995fbc636f58746864067ac8f3b078118b5e9374fb54f4e4c
HACOM_LEGAL_MODEL=Qwen/Qwen3.8-27B-FP8
HACOM_LLM_TIMEOUT=180

# Cấu hình dự phòng Local (nếu offline)
OLLAMA_HOST=http://localhost:11434
```

Kiểm tra kết nối tới Cổng AI HACOM bằng lệnh:
```bash
python test_company_llm.py
```
*(Nếu nhận được mã HTTP 200 và phản hồi từ model `Qwen/Qwen3.8-27B-FP8` là kết nối thành công 100%).*

---

### 3️⃣ Khởi chạy Ứng dụng

#### 🔹 Cách 1: Chạy trực tiếp trên máy trạm Windows (Development)
```bash
python app.py
```
*Hoặc nhấp đúp vào file `start_hacom_legal.bat`.*

#### 🔹 Cách 2: Treo chạy ngầm trên Server Linux (`admin123-PowerEdge-R760` / PM2)
```bash
cd ~/HacomLegalCopilot
pm2 start app.py --name "hacom-legal" --interpreter /home/vinhnv/HacomLegalCopilot/.venv/bin/python
pm2 save
```

#### 🔹 Cách 3: Mở đường link chia sẻ ngoài (Cloudflare Tunnel)
```bash
pm2 start "cloudflared tunnel --url http://localhost:8005" --name "hacom-cf"
pm2 save
pm2 logs hacom-cf --lines 20
```

---

## 🌐 ĐỊA CHỈ TRUY CẬP HỆ THỐNG

Sau khi khởi động, mở trình duyệt web và truy cập:

| Môi trường | Địa chỉ (URL) | Ghi chú |
| :--- | :--- | :--- |
| **Máy cục bộ (Localhost)** | [http://127.0.0.1:8005/](http://127.0.0.1:8005/) | Mặc định trên máy phát triển |
| **Mạng Server Công ty** | `http://27.72.146.12:8005/` | Truy cập qua IP máy chủ PowerEdge R760 |
| **Đường hầm Cloudflare** | `https://*.trycloudflare.com` | Link public mã hóa an toàn để test từ xa |

---

## 📋 HƯỚNG DẪN SỬ DỤNG 3 CHỨC NĂNG CHÍNH

### 🔍 1. Tab 1: Tra cứu Pháp lý RAG (Verified Legal RAG)
* **Mô tả**: Hỗ trợ chuyên viên và lãnh đạo hỏi đáp các tình huống pháp lý phức tạp.
* **Tính năng**:
  * Bộ lọc chuyên sâu theo 7 nhóm lĩnh vực: *Quy hoạch - Đất đai, Đầu tư - Đấu thầu, Nhà ở xã hội, BĐS Nghĩ dưỡng & KĐT, Xây dựng - Giấy phép, Năng lượng tái tạo, Môi trường - PCCC*.
  * Thẻ gợi ý câu hỏi mẫu thông minh: Bấm trực tiếp để tự động điền và phân tích ngay.
  * Thẻ trích dẫn căn cứ pháp lý (`Verified Source Cards`) hiển thị trích dẫn nguyên văn, số hiệu văn bản, ngày ban hành và ngày có hiệu lực.
  * Tích hợp cơ chế **Universal Modal Viewer**: Bấm vào bất kỳ điều luật nào để đọc toàn văn văn bản gốc mà không cần mở file rời.

### 🚨 2. Tab 2: Cảnh báo Tác động Văn bản Luật Mới
* **Mô tả**: Đánh giá đa chiều tác động của một luật/nghị định mới ban hành lên danh mục 7 dự án trọng điểm của HACOM (*KĐT K1, KĐT K2, Hacom GalaCity, Điện gió Hòa Thắng, KDL Bình Sơn Ocean Park, Cụm CN Tháp Chàm...*).
* **Cơ chế phân cấp rủi ro (4 cấp độ)**:
  * 🔴 **Đỏ (Rủi ro cao / Khẩn cấp)**: Ảnh hưởng trực tiếp đến nghĩa vụ tài chính, thủ tục điều chỉnh dự án hoặc điều kiện kinh doanh.
  * 🟡 **Vàng (Cần theo dõi / Cảnh báo)**: Thay đổi về trình tự phê duyệt, yêu cầu cập nhật hồ sơ hoặc báo cáo bổ sung.
  * 🟢 **Xanh lá (Thuận lợi / Đòn bẩy)**: Quy định tạo cơ chế thông thoáng, rút ngắn thời gian giải quyết thủ tục hoặc ưu đãi thuế/đất.
  * 🔵 **Xanh dương (Thông tin / Tham chiếu)**: Thay đổi mang tính kỹ thuật, quy chuẩn nội bộ hoặc mở rộng phạm vi áp dụng.

### 🕸️ 3. Tab 3: Đồ thị Tri thức & Xử lý Xung đột Pháp lý
* **Mô tả**: Trực quan hóa mối quan hệ giữa 19 văn bản quy phạm pháp luật nền tảng.
* **Tính năng**:
  * Hiển thị các mối quan hệ: `AMENDS` (Sửa đổi, bổ sung), `GUIDES` (Quy định chi tiết / hướng dẫn thi hành), `CONFLICT_WITH` (Xung đột quy định).
  * Quy tắc ưu tiên theo Điều 156 Luật Ban hành VBQPPL 2015.
  * Bấm trực tiếp vào các nút hoặc liên kết trên đồ thị để mở bảng tra cứu toàn văn điều luật tương ứng.

---

## 📂 CẤU TRÚC MÃ NGUỒN DỰ ÁN

```
HacomLegalCopilot/
├── app.py                         # Điểm khởi động chính máy chủ FastAPI + Uvicorn (:8005)
├── app_api.py                     # Định nghĩa RESTful API và giao diện Web Dashboard HACOM
├── verified_rag.py                # Bộ máy Tra cứu RAG 4 lớp kết nối HACOM Internal LLM
├── alert_engine.py                # Động cơ đánh giá tác động 4 cấp độ lên dự án HACOM
├── legal_precedence_engine.py     # Động cơ giải quyết xung đột theo Điều 156 Luật Ban hành VBQPPL
├── knowledge_graph.py             # Quản trị Đồ thị Tri thức pháp lý (Nodes, Edges, Conflicts)
├── vector_store.py                # Kho chỉ mục Vector & Hybrid Search trên 1.181 chunks
├── pdf_parser.py                  # Module bóc tách cấu trúc Chương/Mục/Điều/Khoản từ PDF
├── vietlex_client.py              # Module tích hợp tra cứu văn bản pháp luật
├── config.py                      # Cấu hình đường dẫn và biến môi trường toàn cục
├── test_company_llm.py            # Script kiểm thử kết nối Cổng LLM Tập đoàn HACOM
├── API_LLM_HACOM.md               # Tài liệu đặc tả kỹ thuật Cổng LLM Tập đoàn
├── BAO_CAO_NGHIEM_THU_TICH_HOP_LLM_HACOM.md # Báo cáo nghiệm thu kỹ thuật
├── Report_LLMHacom.docx           # Báo cáo nghiệm thu định dạng Microsoft Word gửi Lãnh đạo
├── requirements.txt               # Danh sách thư viện Python phụ thuộc
├── start_hacom_legal.bat          # Kịch bản khởi động 1-Click trên Windows
├── .env.example                   # Mẫu cấu hình biến môi trường chuẩn
├── .gitignore                     # Cấu hình loại trừ tệp nhạy cảm và cache khi đẩy Git
└── data/
    ├── legal_knowledge_graph.json # Dữ liệu đồ thị tri thức (19 nodes, các quan hệ văn bản)
    └── legal_vector_store/
        └── legal_chunks_index.json # 1.181 chunks điều khoản đã được chuẩn hóa và số hóa 100%
```

---

## 🛡️ AN TOÀN THÔNG TIN & BẢO MẬT

1. **Bảo vệ API Key**: Tệp `.env` chứa chuỗi khóa `HACOM_LLM_KEY` được đưa vào `.gitignore` và không bao giờ đẩy lên kho mã nguồn công khai.
2. **Hạ tầng On-Premise**: Toàn bộ luồng suy luận của AI chạy trên hạ tầng máy chủ GPU của HACOM Holdings (`ai.hacomholdings.com.vn`), tuân thủ 100% chính sách bảo mật thông tin nội bộ của Tập đoàn.

---
*© 2026 Tập đoàn HACOM Holdings. Tài liệu phục vụ nội bộ Ban Pháp chế Dự án và Ban Công nghệ Thông tin.*
