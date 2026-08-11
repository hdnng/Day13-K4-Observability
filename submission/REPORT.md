# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: konichiwa
- Repository URL: https://github.com/hdnng/Day13-K4-Observability
- Commit SHA cuối: `77e8fe1ab1fef86be73a6fbf0d2562dc8e120803`
- Thành viên và vai trò:
  - Trần Duy Sơn - 2A202601792: M1 (Logging & PII)
  - Sái Hoài Nam - 2A202601993: M2 (Tracing & Prompt Version)
  - Phạm Hoàng Nam - 2A202601442: M3 (Dashboard, SLO & Alert)
  - Dương Ngọc Hải - 2A202601748: M4 (Incident, Report & Demo)

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

- Challenge ID: `day13-k4-observability-v1`
- Triệu chứng từ metrics: SLI `latency_p95_ms` bị phá vỡ, bảng dashboard hiển thị thời gian phản hồi API tăng đột biến vượt ngưỡng 2000ms (cụ thể lên tới ~2650ms).
- Trace ID liên quan: `2b5b790465156c0e2f7d4c58c145a6d9`
- Log line/correlation ID liên quan: `req-ae8d4f82`
- Root cause: Quá trình truy xuất dữ liệu từ Vector Store (span `retrieve` trong hệ thống RAG) bị thắt cổ chai, mất thời gian rất dài (2.5s) để phản hồi, kéo theo toàn bộ API bị chậm. (Mô phỏng lỗi do sự cố database thông qua kịch bản `rag_slow`).
- Fix action: Nâng cấp cấu hình tài nguyên hoặc tối ưu hoá index của Vector Database. Khởi động lại service RAG nếu phát hiện bị treo.
- Preventive measure: Thiết lập timeout cứng cho hàm `retrieve` (ví dụ: tối đa 1.5 giây). Nếu quá giờ sẽ trả về kết quả mặc định (fallback) để tránh treo toàn bộ request và làm nghẽn connection pool. Bổ sung alert rule cảnh báo riêng cho span `retrieve`.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Trần Duy Sơn - 2A202601792 - Son (M1 — Logging & PII) | CP0: Lưu điểm baseline 30/100 vào REPORT.md. <br>CP1: Hoàn thiện logic logging & PII redaction (ẩn email, sđt, CCCD). <br>CP2 (Hỗ trợ): Xác nhận log format khớp với yêu cầu cấu hình Dashboard của M3. | PR #3 (`CP0/Son`)<br>PR #4 (`CP1/Son`)<br>PR #11 (`CP2/Son`) | Cấu hình structlog cần chú ý thứ tự processor để lọc đúng dữ liệu. Contract rõ ràng giúp các role làm việc độc lập. |
| Sái Hoài Nam - 2A202601993 - SaiHoaiNam (M2 — Tracing & Prompt) | CP1: Nghiên cứu cấu trúc code, hoàn thành tìm hiểu về Langfuse SDK (checkpoint 1). <br>CP2: Gắn Langfuse tracing vào API, thiết lập các phiên bản prompt (v1, v2) và tạo ảnh waterfall trace làm bằng chứng. | PR #5 (`CP1/SaiHoaiNam`)<br>PR #8 (`cp2/Nam`) | Thấy rõ sức mạnh của trace waterfall trong việc hiển thị chi tiết thời gian chạy của từng span con. |
| Phạm Hoàng Nam - 2A202601442 - namph (M3 — Dashboard, SLO & Alert) | CP0: Setup venv, bắt baseline `validate_logs` & `validate_dashboard`. <br>CP1 (Hỗ trợ): Nghiên cứu cấu trúc log từ M1 để chuẩn bị build dashboard. <br>CP2: Hoàn thiện `build_dashboard_data.py`, dựng file HTML dashboard, lập SLO và bộ 3 Alert rules. | PR #2 (`CP0/namph`)<br>PR #7 (`CP1/namph`)<br>PR #9 (`CP2/namph`) | Chạy incident thật trên hệ thống cho ra dữ liệu trực quan hơn nhiều so với load test bình thường để build dashboard. |
| Dương Ngọc Hải - 2A202601748 - haidn (M4 — Incident & Report) | CP0: Khởi tạo khung evidence. <br>CP1 & CP2: Báo cáo bằng chứng từ các thành viên. <br>CP3 (Trưởng nhóm sự cố): Kích hoạt challenge `rag_slow`, bắn tải, gắn thêm `@observe` cho module RAG, trích xuất Trace ID/Correlation ID và tổng hợp root cause/fix action vào Báo cáo. | PR #1 (`CP0/haidn`)<br>PR #6 (`CP1/haidn`)<br>PR #10 (`CP2/haidn`)<br>PR #12 (`CP3/haidn`) | Hiểu được bức tranh toàn cảnh: Metrics dùng để báo động, Traces để khoanh vùng nút thắt, và Logs để tìm nguyên nhân gốc rễ. |
