# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py` (baseline CP0): 30/100 — xem `submission/evidence/cp0_baseline.txt`
- Điểm `validate_logs.py` (sau CP1 — M1 hoàn thiện logging/PII): **100/100** — xem `submission/evidence/cp1_validate_logs.txt`
- Điểm `validate_dashboard.py` (baseline CP0): HỢP LỆ 6/6 panel (contract check, chưa phải ảnh dashboard runtime)
- `python -m pytest -q` (baseline CP0): 22 passed
- Tổng số traces:
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID: mỗi request sinh `correlation_id` dạng `req-<8-hex>` trong `app/middleware.py` (ưu tiên header `x-request-id` nếu client gửi sẵn), bind vào structlog contextvars nên xuất hiện xuyên suốt `request_received` → `response_sent` cùng một request, và trả lại qua response header `x-request-id`. Xem `submission/evidence/cp1_sample_logs.jsonl` (2 request mẫu, mỗi request 2 dòng log cùng `correlation_id`, ví dụ `req-c78907c1`).
- Evidence PII redaction: `app/pii.py` che email/SĐT VN/CCCD/thẻ tín dụng (+ passport, địa chỉ VN) qua `scrub_text`; processor `scrub_event` được đăng ký trong `app/logging_config.py` để scrub trước khi JSON được render/ghi file. Dòng đầu `cp1_sample_logs.jsonl` cho thấy `"My email is [REDACTED_EMAIL]"` thay vì email thật.
- Evidence trace waterfall: (thuộc phần M2 — chưa điền, chờ bàn giao)
- Giải thích một span đáng chú ý: (thuộc phần M2 — chưa điền)

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: version 1, label `baseline`
- Version/label candidate: version 2, label `candidate`
- Trace baseline v1: xem `submission/evidence/m2_trace_baseline_v1.png`
- Trace candidate v2: xem `submission/evidence/m2_trace_candidate_v2.png`
- Danh sách tối thiểu 10 traces: xem `submission/evidence/m2_10_traces_list.png`
- Bằng chứng đổi label production sang v2: xem `submission/evidence/m2_production_switched_to_v2.png`
- Bằng chứng rollback production về v1: xem `submission/evidence/m2_production_rollback_to_v1.png`

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| namph (M3 — Dashboard, SLO & Alert) | CP0: dựng venv (Python 3.12), cài dependencies, tạo `.env`, chạy API + load test, lấy baseline `validate_logs.py` (30/100) và `validate_dashboard.py` (6/6 panel hợp lệ), xác nhận `pytest` 22 passed | (branch `CP0/namph`) | Python 3.14 chưa có wheel cho `pydantic-core` (PyO3 giới hạn ≤3.13) nên phải dùng Python 3.12 cho venv |
