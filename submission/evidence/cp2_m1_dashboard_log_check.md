# CP2 — M1 hỗ trợ M3: kiểm tra log format cho Dashboard

M1 (Son) chạy lại đúng quy trình tái tạo evidence trong `docs/dashboard-spec.md`
(baseline → `rag_slow` → `tool_fail` → về baseline) trên log mới sinh ra sau khi
CP1 đã hoàn thiện correlation ID / enrichment / PII redaction, để xác nhận
`data/logs.jsonl` vẫn khớp đúng field mà `scripts/build_dashboard_data.py` và
`config/dashboard.yaml` cần. Không phát hiện sai lệch, không cần sửa `app/`.

## Đối chiếu field

| Panel cần (`config/dashboard.yaml`) | Field log thực tế | Khớp? |
|---|---|---|
| `response_sent.latency_ms` | có, kiểu số nguyên | OK |
| `request_received` (đếm traffic) | có, đúng event name | OK |
| `request_failed.error_type` | có, log trực tiếp `error_type=RuntimeError` | OK |
| `response_sent.cost_usd` | có | OK |
| `response_sent.tokens_in/tokens_out` | có | OK |
| `response_sent.quality_score` | có | OK |
| `incident_enabled/disabled.payload.name` (M3 dùng vẽ vùng incident) | có, đúng cấu trúc | OK |

## Kết quả chạy thật (log mới, có incident thật)

- `rag_slow` bật → P95 latency vọt lên **2651ms** (tăng rõ rệt so với baseline
  ~150ms, đúng như `DASHBOARD_SETUP.md` mô tả).
- `tool_fail` bật → 10 request trả `500 RuntimeError`; `build_dashboard_data.py`
  tính `error_rate_pct = 25.0`, `breakdown = {"RuntimeError": 10}` — khớp
  chính xác số request lỗi đã gửi.
- `python scripts/build_dashboard_data.py`: chạy sạch, không lỗi field/type,
  xuất đủ 6 panel.
- `python scripts/validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard
  contract.`
- `python -m pytest -q`: `22 passed`.

## Lưu ý

Trong lúc verify, `submission/evidence/dashboard_data.json` (evidence gốc của
M3) bị ghi đè tạm bởi dữ liệu test của M1. Đã `git checkout` khôi phục lại
đúng bản gốc của M3 ngay sau đó — không có gì thay đổi ở evidence dashboard
chính thức.

## Kết luận

Log format hiện tại (sau CP1) đã hoàn toàn khớp yêu cầu Dashboard của M3,
không cần chỉnh sửa `app/` hay `config/`.
