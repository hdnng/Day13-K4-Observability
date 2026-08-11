# CP1 — Nghiên cứu cấu trúc log (M3 hỗ trợ, chuẩn bị Dashboard)

Vai trò: Thành viên 3 (M3 — Dashboard, SLO & Alert)
Branch: `CP1/namph` (rebase từ `develop` sau khi PR #4 `CP1/Son` merge)
Mục tiêu block này (0:30–1:30) theo TASK_DIVISION.md: M1 (Son) chủ trì sửa
`app/` để log có correlation ID, enrichment và PII redaction. Việc của M3 là
nghiên cứu cấu trúc log thật do M1 sinh ra để chuẩn bị build Dashboard ở
CP2 — không sửa code trong `app/`.

## 1. Xác nhận kết quả CP1 (đã merge, code của Son)

Chạy lại toàn bộ luồng CP1 trên máy mình để lấy log thật (không sửa code):

```
rm data/logs.jsonl
uvicorn app.main:app --reload --env-file .env
python scripts/load_test.py
python scripts/validate_logs.py
```

Kết quả `validate_logs.py`:

```
Total log records analyzed: 21
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 10
Potential PII leaks detected: 0

+ [PASSED] Basic JSON schema
+ [PASSED] Correlation ID propagation
+ [PASSED] Log enrichment
+ [PASSED] PII scrubbing

Estimated Score: 100/100
```

→ Vượt mục tiêu ≥80/100 của CHECKPOINTS.md. Đây là bằng chứng của M1, ghi lại
ở đây chỉ để làm căn cứ cho nghiên cứu cấu trúc log dưới đây.

## 2. Cấu trúc log thật (ví dụ dòng `response_sent`)

```json
{
  "service": "api",
  "latency_ms": 150,
  "tokens_in": 36,
  "tokens_out": 85,
  "cost_usd": 0.001383,
  "quality_score": 0.9,
  "payload": {"answer_preview": "..."},
  "event": "response_sent",
  "session_id": "s01",
  "feature": "qa",
  "correlation_id": "req-8f8b98f9",
  "env": "dev",
  "model": "claude-sonnet-4-5",
  "user_id_hash": "2055254ee30a",
  "level": "info",
  "ts": "2026-08-11T08:49:39.556548Z"
}
```

Ba loại `event` xuất hiện trong một lần chạy load test bình thường (không
bật incident): `app_started`, `request_received`, `response_sent`.
`request_failed` (với field `error_type`) chỉ xuất hiện khi có lỗi/incident —
sẽ cần inject incident thật ở CP2/CP3 để thấy dòng này.

## 3. Ánh xạ field → 6 panel Dashboard (từ `config/dashboard.yaml`)

| # | Panel | Event cần lọc | Field dùng | Threshold hiện tại | Đã xác nhận có trong log thật? |
|---|---|---|---|---|---|
| 1 | Latency | `response_sent` | `latency_ms` | p95 ≤ 3000ms | ✅ có |
| 2 | Traffic | `request_received` | đếm số dòng theo phút | ≥ 1 req/phút | ✅ có |
| 3 | Error | `request_received`, `request_failed` | `error_type` | error_rate_pct ≤ 2% | ⚠️ chưa thấy `request_failed` trong run bình thường — cần inject incident để kiểm tra field `error_type` |
| 4 | Cost | `response_sent` | `cost_usd` | tổng ≤ $2.5 | ✅ có |
| 5 | Tokens | `response_sent` | `tokens_in`, `tokens_out` | tổng ≤ 50,000 | ✅ có |
| 6 | Quality | `response_sent` | `quality_score` | trung bình ≥ 0.75 | ✅ có (mẫu = 0.9) |

## 4. Quan sát quan trọng cho CP2

- `correlation_id` đã unique cho mỗi request (10/10 request test có ID khác
  nhau) — panel không bắt buộc phải hiển thị field này nhưng nó là chìa khóa
  để từ Dashboard → lọc log cụ thể khi điều tra incident ở CP3.
- `user_id_hash`, `session_id`, `feature`, `model`, `env` đã enrich đầy đủ
  trên mọi dòng log của một request (nhờ `bind_contextvars` trong
  `app/main.py::chat()`), có thể dùng để breakdown panel Traffic/Error theo
  `feature` nếu muốn mở rộng.
- PII đã được redact ở tầng `scrub_event` (structlog processor) trước khi ghi
  file — `payload.answer_preview`/`message_preview` không lộ email/SĐT/thẻ.
  Điều này quan trọng vì Dashboard chỉ đọc từ `data/logs.jsonl`, nên panel sẽ
  không vô tình hiển thị dữ liệu nhạy cảm.
- Panel Error (#3) cần được kiểm tra thực tế với `request_failed` — sẽ làm ở
  đầu CP2 bằng cách bật một scenario lỗi tạm thời (ví dụ
  `python scripts/inject_incident.py --scenario tool_fail`), quan sát field
  `error_type`, rồi tắt lại incident trước khi tiếp tục.
- Không cần sửa `config/dashboard.yaml` ở bước này — schema field đã khớp
  100% với log thật do M1 sinh ra, ngoại trừ điểm cần xác minh thêm ở trên.

## 5. Việc KHÔNG làm ở block này (tránh đụng CP1 của M1)

- Không sửa `app/middleware.py`, `app/main.py`, `app/logging_config.py`,
  `app/pii.py`, `app/metrics.py` — toàn bộ đã hoàn thiện bởi Son (PR #4).
- Không tự chấm điểm lại CP1 để nộp thay M1 — số liệu ở mục 1 chỉ dùng làm
  input cho nghiên cứu Dashboard.
