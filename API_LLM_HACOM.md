# API LLM HACOM

Endpoint tương thích OpenAI, chuyển tiếp tới Qwen3.8-27B chạy trên máy chủ HACOM.
Dữ liệu không rời khỏi hạ tầng nội bộ.

Tài liệu tích hợp · v1 · 26/08/2026

---

## Mục lục

- [Bắt đầu](#bắt-đầu)
- [Ranh giới](#ranh-giới)
- [Endpoint](#endpoint)
- [Tham số](#tham-số)
- [Streaming](#streaming)
- [Tool calling](#tool-calling)
- [Chế độ suy luận](#chế-độ-suy-luận)
- [Hạn mức](#hạn-mức)
- [Mã lỗi](#mã-lỗi)
- [Thực hành tốt](#thực-hành-tốt)
- [Hỗ trợ](#hỗ-trợ)

---

## Bắt đầu

API theo chuẩn OpenAI Chat Completions, nên mọi SDK OpenAI dùng được không cần sửa gì
ngoài `base_url` và `api_key`.

| | |
|---|---|
| **base_url** | `https://ai.hacomholdings.com.vn/api/llm/v1` |
| **api_key** | HACOM cấp riêng, chuỗi hex 64 ký tự |
| **model** | `Qwen/Qwen3.8-27B-FP8` |

### Phép thử kết nối (chạy cái này trước)

`GET /models` không chạm GPU nên trả lời tức thì. Chạy từ **server sẽ gọi API**, không phải
từ máy cá nhân — nó kiểm cùng lúc cả DNS, TLS, đường mạng ra ngoài và key.

```bash
curl -sS -w '\nhttp %{http_code}\n' \
  https://ai.hacomholdings.com.vn/api/llm/v1/models \
  -H "Authorization: Bearer $HACOM_LLM_KEY"
```

| Kết quả | Nghĩa |
|---|---|
| `http 200` kèm JSON có `Qwen/Qwen3.8-27B-FP8` | Xong, chuyển sang phần dưới |
| `http 404` | Key sai hoặc thiếu header. Kiểm lại chuỗi key và tiền tố `Bearer `. |
| `Could not resolve host` | DNS phía bạn không ra được. Kỳ vọng `ai.hacomholdings.com.vn` → `27.72.146.12`. |
| `Connection timed out` | Firewall phía bạn chặn ra ngoài cổng 443, hoặc cần đi qua proxy nội bộ. |
| Lỗi chứng chỉ | Đồng hồ hệ thống sai, hoặc CA store quá cũ. Chứng chỉ là Let's Encrypt, không cần cài gì thêm. |

### Python

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://ai.hacomholdings.com.vn/api/llm/v1",
    api_key=os.environ["HACOM_LLM_KEY"],
)

resp = client.chat.completions.create(
    model="Qwen/Qwen3.8-27B-FP8",
    messages=[
        {"role": "system", "content": "Bạn là trợ lý nội bộ, trả lời ngắn gọn."},
        {"role": "user", "content": "Xin chào"},
    ],
    max_tokens=256,
)
print(resp.choices[0].message.content)
```

### TypeScript

```ts
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://ai.hacomholdings.com.vn/api/llm/v1",
  apiKey: process.env.HACOM_LLM_KEY!,
});

const resp = await client.chat.completions.create({
  model: "Qwen/Qwen3.8-27B-FP8",
  messages: [{ role: "user", content: "Xin chào" }],
  max_tokens: 256,
});
console.log(resp.choices[0].message.content);
```

### curl

```bash
curl -X POST https://ai.hacomholdings.com.vn/api/llm/v1/chat/completions \
  -H "Authorization: Bearer $HACOM_LLM_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"Qwen/Qwen3.8-27B-FP8",
       "messages":[{"role":"user","content":"Xin chào"}],
       "max_tokens":256}'
```

> **Giữ key ở biến môi trường.** Đừng đưa vào repo, không gửi qua chat nhóm, không nhúng
> vào ứng dụng phía client — key nằm trong bundle JavaScript là key công khai. Mọi lệnh gọi
> phải đi từ server của bạn.

---

## Ranh giới

Đọc mục này trước khi thiết kế tính năng. Đây là **model thuần**, không phải hệ thống
hỏi-đáp tài liệu.

**Có**

- Sinh văn bản, hội thoại nhiều lượt, tiếng Việt và tiếng Anh
- Streaming SSE tương thích SDK OpenAI
- Tool calling, JSON mode, chuỗi suy luận
- System prompt của bạn được chuyển nguyên văn
- Dữ liệu xử lý tại chỗ, không gửi ra nhà cung cấp bên ngoài

**Không**

- **Không truy hồi tài liệu HACOM.** Hỏi "quy định nghỉ phép của HACOM" sẽ được trả lời
  bằng kiến thức chung của model, có thể sai hoàn toàn. Muốn model dựa trên văn bản nào
  thì tự đưa văn bản đó vào prompt.
- **Không lưu lịch sử hội thoại.** Mỗi request độc lập; bạn tự giữ và gửi lại toàn bộ
  lượt trước.
- Không có embeddings, không có rerank, không upload file
- Không có `/completions` (chỉ `/chat/completions`)

---

## Endpoint

| Method | Đường dẫn | Mô tả |
|---|---|---|
| `POST` | `/chat/completions` | Sinh câu trả lời. Đặt `stream: true` để nhận SSE. |
| `GET` | `/models` | Danh sách model khả dụng. |

Cả hai đều yêu cầu header `Authorization: Bearer <key>`. Không có endpoint nào khác;
đường dẫn khác trả 404.

```json
GET /models
{"object":"list","data":[{"id":"Qwen/Qwen3.8-27B-FP8","object":"model","owned_by":"hacom"}]}
```

---

## Tham số

Chỉ những trường dưới đây được chuyển tới model. Trường ngoài danh sách bị **bỏ qua và
không báo lỗi** — request vẫn trả 200, nên nếu một tham số không có tác dụng, hãy đối
chiếu bảng này trước.

| Trường | Ghi chú |
|---|---|
| `messages` | **Bắt buộc.** Mảng không rỗng, mỗi phần tử có `role`. Vai trò: `system`, `user`, `assistant`, `tool`. |
| `max_tokens` | Số token sinh ra tối đa. Trần 2048 — xin lớn hơn thì bị hạ xuống 2048, không báo lỗi. Bỏ trống cũng thành 2048. |
| `stream` | `true` để nhận SSE. |
| `temperature` | 0 tới 2. Việc phân loại, trích xuất nên dùng 0–0.3. |
| `top_p`, `top_k` | Lấy mẫu hạt nhân và top-k. |
| `stop` | Chuỗi hoặc mảng chuỗi dừng. Phần khớp *không* có trong kết quả; `finish_reason` vẫn là `stop`. |
| `seed` | Cùng seed + cùng tham số cho kết quả lặp lại được. |
| `presence_penalty`<br>`frequency_penalty`<br>`repetition_penalty` | Giảm lặp lại. |
| `n` | Số phương án trả về. Mỗi phương án tính vào ngân sách token. |
| `logprobs`, `top_logprobs` | Xác suất token. |
| `response_format` | `{"type":"json_object"}` buộc kết quả là JSON hợp lệ. |
| `tools`, `tool_choice`<br>`parallel_tool_calls` | Xem mục [Tool calling](#tool-calling). |
| `chat_template_kwargs` | Xem mục [Chế độ suy luận](#chế-độ-suy-luận). |
| `model` | Nhận nhưng bị bỏ qua — luôn dùng model đang phục vụ. Cứ gửi để SDK không báo thiếu. |

---

## Streaming

Đặt `stream: true`, kết quả là SSE chuẩn OpenAI: mỗi dòng `data: {…}` chứa một chunk với
`choices[0].delta.content`, kết thúc bằng `data: [DONE]`.

```python
stream = client.chat.completions.create(
    model="Qwen/Qwen3.8-27B-FP8",
    messages=[{"role": "user", "content": "Đếm từ 1 đến 5."}],
    max_tokens=64,
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

> Nếu bạn tự đọc SSE thay vì dùng SDK: **đừng đệm cả phản hồi** rồi mới xử lý, và nhớ rằng
> một chunk có thể tới sau vài giây im lặng khi hệ thống đang xếp hàng. Đặt timeout đọc
> theo *khoảng lặng giữa hai chunk*, không theo tổng thời gian.

---

## Tool calling

Hỗ trợ theo chuẩn OpenAI. Model trả về `message.tool_calls`; bạn thực thi hàm rồi gửi kết
quả lại bằng message có `role: "tool"`.

```python
tools = [{
    "type": "function",
    "function": {
        "name": "tra_cuu_don_hang",
        "description": "Tra cứu trạng thái đơn hàng theo mã",
        "parameters": {
            "type": "object",
            "properties": {"ma_don": {"type": "string"}},
            "required": ["ma_don"],
        },
    },
}]

resp = client.chat.completions.create(
    model="Qwen/Qwen3.8-27B-FP8",
    messages=[{"role": "user", "content": "Đơn HD123 đến đâu rồi?"}],
    tools=tools,
    tool_choice="auto",
    max_tokens=256,
)
calls = resp.choices[0].message.tool_calls
# [ChatCompletionMessageToolCall(function=Function(
#     name='tra_cuu_don_hang', arguments='{"ma_don": "HD123"}'))]
```

Lược đồ tool cũng chiếm token trong ngân sách 16.384 — bộ tool lớn sẽ ăn vào phần dành
cho hội thoại.

---

## Chế độ suy luận

Qwen3 sinh được một chuỗi suy luận riêng trước khi trả lời. Cổng **mặc định tắt** để tiết
kiệm token và giảm thời gian chờ. Bật khi cần:

```python
extra_body={"chat_template_kwargs": {"enable_thinking": True}}
```

Khi bật, chuỗi suy luận nằm ở `message.reasoning`, câu trả lời vẫn ở `message.content`.
Suy luận tính vào `max_tokens`, nên nếu bật mà để `max_tokens` nhỏ thì `content` có thể bị
cắt hoặc rỗng — tăng `max_tokens` lên khi bật.

Chỉ nên bật cho bài toán nhiều bước (tính toán, suy luận logic). Với phân loại, trích
xuất, viết lại thì để tắt.

---

## Hạn mức

| Giới hạn | Giá trị | Vượt thì sao |
|---|---|---|
| Ngữ cảnh | 16.384 token | `400` — tính cả prompt, lược đồ tool và phần sinh ra |
| Độ dài prompt | 24.000 ký tự | `413` kèm số ký tự thực tế |
| `max_tokens` | 2.048 | Bị hạ âm thầm, không báo lỗi |
| Số request | 300 / 300 giây | `429` kèm header `Retry-After` |
| Đồng thời | 6 | Chờ tối đa 20 giây, hết thì `503` |
| Timeout | 180 giây | Mỗi request |

> **Sáu slot đồng thời là dùng chung với người dùng nội bộ HACOM.** Bạn không thể chiếm hết
> GPU, nhưng vào giờ cao điểm request sẽ chậm hơn. Đừng thiết kế tính năng cần nhiều lệnh
> gọi song song; xếp hàng phía bạn thì mượt hơn là để cổng trả 503.

Hai trần ký tự và token độc lập nhau. Văn bản dày ký tự (mã nguồn, chữ Hán) có thể **dưới**
24.000 ký tự mà vẫn vượt 16.384 token và nhận `400`.

---

## Mã lỗi

| Mã | Nghĩa | Xử lý |
|---|---|---|
| `404` | Key sai, thiếu key, hoặc sai đường dẫn | Kiểm header `Authorization: Bearer` và `base_url`. Không thử lại tự động — 404 ở đây không bao giờ tự khỏi. |
| `400` | Thân request sai, hoặc vượt 16.384 token | Thông điệp có số token thực tế. Cắt lịch sử hội thoại rồi gửi lại. |
| `413` | Prompt vượt 24.000 ký tự | Thông điệp có cả số thực tế và trần. Cắt theo đó, đừng thử lại nguyên văn. |
| `429` | Vượt hạn mức số request | Chờ đúng số giây trong `Retry-After`. Thử lại ngay chỉ làm hạn mức lâu hồi phục hơn. |
| `503` | Hết slot GPU sau khi đã chờ 20 giây | Thử lại với backoff luỹ tiến (2s, 4s, 8s…). Đây là trạng thái tạm thời. |
| `502` | Model phía sau lỗi hoặc không phản hồi | Báo HACOM kèm thời điểm. Thử lại 1–2 lần rồi dừng. |

Mọi lỗi đều theo hình dạng OpenAI, nên `err.message` của SDK đọc được trực tiếp:

```json
{"error": {"message": "This model's maximum context length is 16384 tokens. However, you requested 10 output tokens and your prompt contains at least 16375 input tokens…", "type": "BadRequestError", "param": "input_tokens"}}
```

```json
{"error": {"message": "Prompt 25000 ký tự, vượt trần 24000. Hãy rút ngắn ngữ cảnh.", "type": "invalid_request_error"}}
```

---

## Thực hành tốt

- **Tự cắt lịch sử hội thoại.** Không có bộ nhớ phía server, nên hội thoại dài sẽ tự đâm
  vào trần 16.384 token. Giữ N lượt gần nhất, hoặc tóm tắt các lượt cũ thành một message
  `system`.
- **Ước lượng token trước khi gửi.** Tiếng Việt xấp xỉ 3 ký tự một token; tiếng Anh xấp xỉ
  4. Trần 24.000 ký tự thường chạm trước trần token, nhưng văn bản dày ký tự thì ngược lại.
- **Đặt `temperature` thấp cho việc cần chính xác.** Phân loại, trích xuất, chuyển định
  dạng nên dùng 0–0.3 và kèm `seed` nếu cần lặp lại được.
- **Dùng `response_format` thay vì dặn model trả JSON.** Nó ràng buộc ở tầng sinh token,
  chắc hơn mọi câu nhắc trong prompt.
- **Đừng dựa vào model để biết dữ liệu nội bộ.** Cần thông tin HACOM thì đưa văn bản vào
  prompt; model không đọc được gì ngoài những gì bạn gửi.
- **Ghi log `usage` của mỗi lệnh gọi.** Khi cần điều chỉnh hạn mức, đó là số liệu để nói
  chuyện.

---

## Hỗ trợ

Khi báo lỗi, gửi kèm bốn thứ này thì phía HACOM tra được ngay trong log:

- Thời điểm (kèm múi giờ) và mã lỗi HTTP
- `id` trong phản hồi, nếu có (dạng `chatcmpl-…`)
- Thân request đã lược nội dung nhạy cảm — giữ lại các tham số
- Thông điệp lỗi nguyên văn

**Đừng gửi key trong báo cáo lỗi.** Nếu nghi key bị lộ, báo HACOM để thu hồi — việc đó chỉ
mất một lần sửa cấu hình và restart, phía bạn chỉ cần đổi chuỗi key.

---

Phiên bản tài liệu v1, 26/08/2026. Hạn mức và trần có thể thay đổi; HACOM sẽ thông báo
trước khi siết. Model `Qwen/Qwen3.8-27B-FP8` chạy trên vLLM tại hạ tầng HACOM.
