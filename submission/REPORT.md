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
- Tổng số traces: > 10 (xem `submission/evidence/m2_10_traces_list.png`)
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `submission/evidence/dashboard.html`

## 3. Logging và tracing

- Evidence correlation ID: mỗi request sinh `correlation_id` dạng `req-<8-hex>` trong `app/middleware.py` (ưu tiên header `x-request-id` nếu client gửi sẵn), bind vào structlog contextvars nên xuất hiện xuyên suốt `request_received` → `response_sent` cùng một request, và trả lại qua response header `x-request-id`. Xem `submission/evidence/cp1_sample_logs.jsonl` (2 request mẫu, mỗi request 2 dòng log cùng `correlation_id`, ví dụ `req-c78907c1`).
- Evidence PII redaction: `app/pii.py` che email/SĐT VN/CCCD/thẻ tín dụng (+ passport, địa chỉ VN) qua `scrub_text`; processor `scrub_event` được đăng ký trong `app/logging_config.py` để scrub trước khi JSON được render/ghi file. Dòng đầu `cp1_sample_logs.jsonl` cho thấy `"My email is [REDACTED_EMAIL]"` thay vì email thật.
- Evidence trace waterfall: xem `submission/evidence/m2_trace_candidate_v2.png` và `submission/evidence/m2_trace_baseline_v1.png`
- Giải thích một span đáng chú ý: Span `retrieve` (hoặc `generation`) trong trace waterfall cho phép xác định chính xác thời gian RAG hoặc gọi LLM mất bao lâu. Ví dụ, khi M3 bật incident `rag_slow`, span `retrieve` sẽ phình to rõ rệt (>2.5s), giúp khoanh vùng nguyên nhân sự cố nhanh chóng thay vì chỉ nhìn thấy tổng latency tăng.

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

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: `submission/evidence/dashboard.html` (dashboard HTML tự dựng, style Looker/shadcn — 6 stat tile với status/threshold, chart latency P50/P95 theo phút, chart traffic/cost theo phút, bảng error breakdown, table-view accessibility). Dữ liệu nguồn: `submission/evidence/dashboard_data.json`, sinh bằng `python scripts/build_dashboard_data.py` đọc trực tiếp `data/logs.jsonl` (70 request nhận, 60 response thành công, 10 lỗi từ practice scenario `tool_fail`, một đợt `rag_slow` đẩy P95 latency lên rõ rệt trước khi tắt lại).
- SLO đã chọn và lý do: giữ 4 SLI mặc định trong `config/slo.yaml` — `latency_p95_ms` ≤ 3000ms (99.5%/28 ngày, đủ biên độ so với baseline mock LLM ~150ms để không báo động giả nhưng vẫn bắt được spike thật), `error_rate_pct` ≤ 2% (99%/28 ngày, khớp threshold panel Error), `daily_cost_usd` ≤ $2.5 (100%, ngân sách hợp lý cho practice traffic), `quality_score_avg` ≥ 0.75 (95%). Chi tiết lý do từng SLI nằm trong ghi chú (`note`) của `config/slo.yaml`.
- Alert rules và runbook: 3 alert symptom-based trong `config/alert_rules.yaml` — `high_latency_p95` (warning, P95 > 3000ms/5 phút), `elevated_error_rate` (critical, error_rate_pct > 5%/3 phút), `cost_budget_exceeded` (warning, daily_cost_usd > $2.5). Runbook đầy đủ (SLI liên quan, ảnh hưởng người dùng, 3 bước kiểm tra đầu tiên, mitigation, owner) trong `docs/alerts.md`.

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
| namph (M3 — Dashboard, SLO & Alert) | CP1 (hỗ trợ): nghiên cứu cấu trúc log thật sau khi M1 (Son) hoàn thiện CP1, ánh xạ field → 6 panel dashboard, ghi chú chuẩn bị cho CP2 | (branch `CP1/namph`) | Không đụng vào `app/` đang được người khác sửa; validator/log thật là nguồn xác nhận đáng tin hơn suy luận từ schema |
| namph (M3 — Dashboard, SLO & Alert) | CP2: thêm `error_rate_pct` vào `app/metrics.py`; viết `scripts/build_dashboard_data.py` tổng hợp 6 panel từ `data/logs.jsonl`; dựng dashboard HTML (style Looker/shadcn, KPI tile + threshold meter + timeline chart + bảng error + table-view accessibility); điền `docs/dashboard-spec.md`, `config/slo.yaml`, `config/alert_rules.yaml`, `docs/alerts.md`; xác nhận `validate_dashboard.py` 6/6 và `pytest` 22 passed | (branch `CP2/namph`) | Chạy incident thật (`rag_slow`, `tool_fail`) trước khi build dashboard cho ra dữ liệu thuyết phục hơn nhiều so với chỉ chạy load test bình thường |
