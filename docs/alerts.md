# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `high_latency_p95`
- Severity: warning
- SLI/SLO liên quan: `latency_p95_ms` — objective 3000ms, target 99.5% (`config/slo.yaml`)
- Điều kiện và thời gian duy trì: `latency_p95 > 3000ms` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Câu trả lời chậm rõ rệt (từ ~150ms baseline lên hàng giây); trải nghiệm chat cảm thấy "treo"
- Ba bước kiểm tra đầu tiên:
  1. Gọi `curl http://localhost:8000/metrics` xác nhận `latency_p95` hiện tại và so với baseline
  2. Mở Langfuse (nếu có key), lọc trace trong khoảng thời gian bất thường, mở waterfall của trace chậm nhất để xem span nào (retrieve/generate) kéo dài thời gian
  3. Lấy `correlation_id` từ trace/response header, `grep` trong `data/logs.jsonl` để xem log `request_received`/`response_sent` tương ứng có gì bất thường trong payload
- Mitigation tạm thời: Nếu do RAG chậm (giống practice scenario `rag_slow`), tắt tính năng RAG tạm thời hoặc tăng timeout/cache câu trả lời phổ biến; thông báo on-call nếu latency không giảm sau khi tắt incident giả lập
- Owner: on-call-engineer

## Alert 2

- Tên: `elevated_error_rate`
- Severity: critical
- SLI/SLO liên quan: `error_rate_pct` — objective 2%, target 99.0% (`config/slo.yaml`); alert bắn ở ngưỡng cao hơn (5%) vì đây là mức critical, còn 2% là SLO tổng thể theo dõi dài hạn
- Điều kiện và thời gian duy trì: `error_rate_pct > 5` liên tục trong 3 phút
- Ảnh hưởng tới người dùng: Một phần request trả lỗi 500, người dùng không nhận được câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Gọi `/metrics`, xem `error_rate_pct` và `error_breakdown` để biết loại lỗi chiếm đa số (ví dụ `RuntimeError`)
  2. Tìm dòng log `request_failed` gần nhất trong `data/logs.jsonl` (field `error_type`, `payload.detail`) để biết nguyên nhân cụ thể
  3. Kiểm tra `/health` xem incident nào đang bật (`incidents.tool_fail`, v.v.) — nếu là practice/challenge đã biết, xác nhận đúng kịch bản đang chạy
- Mitigation tạm thời: Nếu do dependency giả lập lỗi (giống `tool_fail`), tắt incident (`python scripts/inject_incident.py --scenario tool_fail --disable`) hoặc failover sang fallback response; nếu là lỗi thật, rollback deploy gần nhất
- Owner: on-call-engineer

## Alert 3

- Tên: `cost_budget_exceeded`
- Severity: warning
- SLI/SLO liên quan: `daily_cost_usd` — objective $2.5/ngày, target 100% (`config/slo.yaml`)
- Điều kiện và thời gian duy trì: `daily_cost_usd > 2.5` (kiểm tra theo cửa sổ ngày, không cần chờ nhiều phút)
- Ảnh hưởng tới người dùng: Không ảnh hưởng trực tiếp tới trải nghiệm ngay lập tức, nhưng có rủi ro vượt ngân sách vận hành nếu tiếp diễn
- Ba bước kiểm tra đầu tiên:
  1. Gọi `/metrics`, so sánh `total_cost_usd` và `avg_cost_usd` với baseline bình thường
  2. Xem panel Tokens (`tokens_in_total`, `tokens_out_total`) để biết cost tăng do số lượng request hay do mỗi response sinh nhiều token hơn (giống practice scenario `cost_spike` — output tokens × 4)
  3. Lọc `data/logs.jsonl` theo `feature`/`session_id` để tìm request hoặc user cụ thể tạo phần lớn chi phí
  - Mitigation tạm thời: Giới hạn `max_output_tokens`, bật cache cho câu hỏi lặp lại, hoặc tạm ngắt tính năng đang gây spike (giống `cost_spike`)
- Owner: team-lead
