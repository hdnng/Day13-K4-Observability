# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py` (baseline CP0): 30/100 — xem `submission/evidence/cp0_baseline.txt` (sẽ cập nhật điểm cuối sau CP1)
- Điểm `validate_dashboard.py` (baseline CP0): HỢP LỆ 6/6 panel (contract check, chưa phải ảnh dashboard runtime)
- `python -m pytest -q` (baseline CP0): 22 passed
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

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
