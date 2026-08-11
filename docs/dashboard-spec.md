# Yêu cầu dashboard

Contract có thể kiểm tra bằng máy nằm tại `config/dashboard.yaml`. Hướng dẫn dựng và kiểm tra runtime nằm tại [DASHBOARD_SETUP.md](DASHBOARD_SETUP.md).

Dashboard chính cần đủ 6 nhóm thông tin:

1. Latency P50/P95/P99.
2. Traffic: request count hoặc QPS.
3. Error rate và breakdown theo loại lỗi.
4. Cost theo thời gian.
5. Tổng token input/output.
6. Quality proxy.

Tiêu chuẩn trình bày:

- Khoảng thời gian mặc định: 1 giờ.
- Tự refresh mỗi 15–30 giây nếu công cụ hỗ trợ.
- Có threshold hoặc SLO line.
- Ghi rõ đơn vị.
- Chỉ giữ 6–8 panel quan trọng ở lớp chính.
- Screenshot phải nhìn được tên panel và khoảng thời gian.

Kiểm tra contract trước khi chụp evidence:

```bash
python scripts/validate_dashboard.py
```

## Công cụ và cách dựng (M3 — Dashboard, SLO & Alert)

Công cụ: dashboard HTML tự dựng (không phụ thuộc Grafana/Langfuse), đọc dữ
liệu qua `scripts/build_dashboard_data.py` — script này parse
`data/logs.jsonl`, tổng hợp đúng 6 nhóm chỉ số theo `config/dashboard.yaml`
và xuất `submission/evidence/dashboard_data.json`. File JSON đó được nhúng
tĩnh vào trang dashboard (không gọi API runtime) để có thể chụp evidence và
xem lại bất cứ lúc nào mà không cần server đang chạy.

Evidence dashboard (ảnh chụp + link xem trực tiếp):
`submission/evidence/dashboard_screenshot.png` (nếu có) và ghi chú link
Artifact trong `submission/REPORT.md` mục 5.

## Chi tiết 6 panel

| # | Panel | Nguồn (`data/logs.jsonl`) | Phép tổng hợp | Đơn vị | Threshold / SLO line |
|---|---|---|---|---|---|
| 1 | Latency | `response_sent.latency_ms` | P50, P95, P99 | ms | P95 ≤ 3000ms |
| 2 | Traffic | `request_received` (đếm dòng) | count, theo phút | requests/phút | ≥ 1 req/phút |
| 3 | Error | `request_received`, `request_failed.error_type` | error_rate_pct = failed/received × 100, breakdown theo `error_type` | % | error_rate_pct ≤ 2% |
| 4 | Cost | `response_sent.cost_usd` | tổng theo phút + tổng toàn cửa sổ | USD | tổng ≤ $2.5 |
| 5 | Tokens | `response_sent.tokens_in`, `tokens_out` | tổng theo field | tokens | tổng (in+out) ≤ 50,000 |
| 6 | Quality | `response_sent.quality_score` | trung bình (mean) | score 0–1 | trung bình ≥ 0.75 |

Khoảng thời gian mặc định: **60 phút**. Refresh: **30 giây** (dashboard tĩnh —
refresh bằng cách chạy lại `python scripts/build_dashboard_data.py` sau mỗi
lần load test/incident mới, đúng chu kỳ 30s nếu chạy script theo lịch).

## Cách tái tạo dữ liệu evidence

```bash
rm data/logs.jsonl               # log sạch, tránh dữ liệu cũ lẫn vào
uvicorn app.main:app --reload --env-file .env
python scripts/load_test.py                              # baseline traffic
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py --concurrency 5               # latency spike
python scripts/inject_incident.py --scenario rag_slow --disable
python scripts/inject_incident.py --scenario tool_fail
python scripts/load_test.py --concurrency 5               # error spike
python scripts/inject_incident.py --scenario tool_fail --disable
python scripts/load_test.py                               # về lại baseline
python scripts/build_dashboard_data.py                     # xuất dashboard_data.json
python scripts/validate_dashboard.py                       # xác nhận contract 6/6
```

Dữ liệu evidence hiện tại (`submission/evidence/dashboard_data.json`) được
sinh đúng theo quy trình trên: 70 request nhận, 60 response thành công, 10
request lỗi (`tool_fail` → `RuntimeError`), một đợt `rag_slow` đẩy P95 latency
lên rõ rệt trước khi tắt lại.
