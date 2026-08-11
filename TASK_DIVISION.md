# Phân chia công việc Lab 13: Observability cho hệ thống AI

Bài lab kéo dài 4 giờ, yêu cầu làm việc nhóm hiệu quả. Nhóm gồm 4 thành viên, mỗi người đảm nhận một vai trò chính và phối hợp qua từng checkpoint.

## Các vai trò trong nhóm

1. **Thành viên 1: Logging & PII (M1)** - Chịu trách nhiệm về cấu trúc log, correlation ID và che giấu dữ liệu nhạy cảm (PII).
2. **Thành viên 2: Tracing & Prompt Version (M2)** - Đảm bảo mọi luồng request đều được trace đầy đủ và quản lý phiên bản prompt trên Langfuse.
3. **Thành viên 3: Dashboard, SLO & Alert (M3)** - Chịu trách nhiệm xây dựng dashboard, theo dõi các chỉ số và thiết lập ngưỡng cảnh báo (SLO/Alert).
4. **Thành viên 4: Incident, Report & Demo (M4)** - Quản lý quá trình xử lý sự cố (challenge), điều phối tổng hợp báo cáo và chuẩn bị demo.

---

## Kế hoạch chi tiết theo từng Checkpoint

### Checkpoint 0: Setup và Baseline (0:00 – 0:30)
**Mục tiêu:** Cả nhóm hoàn tất môi trường, hiểu base code và lấy dữ liệu ban đầu.

*   **Tất cả (M1, M2, M3, M4):**
    *   Cài đặt môi trường theo `SETUP.md` (khuyên dùng Langfuse cloud để chia sẻ dễ hơn).
    *   Chạy thử API `uvicorn app.main:app --reload --env-file .env`.
    *   Chạy load test ban đầu bằng `python scripts/load_test.py` để sinh ra `data/logs.jsonl`.
*   **M1 (Logging & PII):**
    *   Chạy lệnh `python scripts/validate_logs.py` để lấy điểm baseline.
    *   Lưu điểm baseline vào `submission/REPORT.md`.
*   **M3 (Dashboard):**
    *   Chạy `python scripts/validate_dashboard.py` để hiểu dashboard contract hiện tại.
*   **M4 (Report & Demo):**
    *   Tạo khung file `submission/REPORT.md` (nếu chưa có) và khởi tạo thư mục `submission/evidence/`.
    *   Kiểm tra `/health` và chụp ảnh evidence đầu tiên (đảm bảo không lộ key).

---

### Checkpoint 1: Logging và PII (0:30 – 1:30)
**Mục tiêu:** Log API đạt chuẩn cấu trúc và an toàn thông tin (PII redaction).

*   **M1 (Logging & PII) - Chủ trì:**
    *   Tìm và hoàn thiện các khối `TODO` liên quan đến log trong thư mục `app/` và `config/`.
    *   Bổ sung *correlation ID* cho request.
    *   Cấu hình JSON log để chứa đủ: `user_id_hash`, `session_id`, `feature`, `model`, `env`.
    *   Viết logic ẩn PII (Email, sđt, thẻ tín dụng).
    *   **Nhiệm vụ:** Chạy lại `python scripts/validate_logs.py` đến khi đạt ít nhất 80/100.
    *   **Bàn giao (Evidence):** File log có correlation ID, log không chứa PII nguyên văn cho M4.
*   **M2, M3, M4 - Hỗ trợ:**
    *   M2: Tìm hiểu trước cấu trúc API để gắn Langfuse SDK.
    *   M3: Nghiên cứu cấu trúc log do M1 đang làm để chuẩn bị build Dashboard từ `data/logs.jsonl`.
    *   M4: Update báo cáo, lưu trữ các screenshot bằng chứng của M1 vào `submission/evidence/`.

---

### Checkpoint 2: Metrics, traces và dashboard (1:30 – 2:30)
**Mục tiêu:** Hoàn thiện Observability (Traces + Metrics Dashboard).

*   **M2 (Tracing & Prompt Version) - Chủ trì Tracing:**
    *   Gắn Langfuse Tracing vào các hàm xử lý API. Đảm bảo chạy đủ 10 traces với metadata hoàn chỉnh.
    *   Tạo prompt v1, v2 trên Langfuse theo `docs/PROMPT_VERSIONING.md`.
    *   Xác minh trace có chứa `prompt_name`, `prompt_label`, `prompt_version`.
    *   Thực hiện thao tác đổi label/rollback prompt trên Langfuse.
    *   **Bàn giao (Evidence):** Chụp waterfall trace, ảnh 2 version prompt, ảnh màn hình thao tác rollback giao cho M4.
*   **M3 (Dashboard, SLO & Alert) - Chủ trì Dashboard:**
    *   Dựng dashboard theo cấu hình `config/dashboard.yaml` (tham khảo `docs/DASHBOARD_SETUP.md`).
    *   Tạo 6 panel (latency, traffic, error, token/cost, quality).
    *   Xác định và vẽ SLO line / ngưỡng threshold.
    *   Chạy `python scripts/validate_dashboard.py` báo hợp lệ 6/6 panel.
    *   **Bàn giao (Evidence):** Chụp ảnh dashboard rõ ràng (có time range, threshold) giao cho M4.
*   **M1, M4 - Hỗ trợ:**
    *   M1: Hỗ trợ M3 nếu log format sinh ra chưa đúng yêu cầu của Dashboard.
    *   M4: Tập hợp toàn bộ bằng chứng từ M2 và M3 đưa vào thư mục `submission/evidence/`.

---

### Checkpoint 3: Challenge chính thức (2:30 – 3:30)
**Mục tiêu:** Phân tích, điều tra và sửa lỗi hệ thống (sau khi Lab Coach release `config/challenge.json`).

*   **Tất cả cùng tham gia (M4 điều phối):**
    *   Khi có file challenge, M4 chạy `python scripts/inject_incident.py` và load test `python scripts/load_test.py --challenge --concurrency 5`.
*   **M3 (Dashboard):** Quan sát Dashboard và Metrics, chỉ ra triệu chứng bất thường (ví dụ: latency vọt lên, error rate tăng) và báo cho nhóm.
*   **M2 (Tracing):** Lên Langfuse, sử dụng khoảng thời gian M3 cung cấp để tìm ra Trace bị lỗi/chậm (khoanh vùng span).
*   **M1 (Logging):** Từ Trace ID của M2, tìm Correlation ID tương ứng trong Log để xác định chính xác nguyên nhân (root cause).
*   **M4 (Incident Lead):**
    *   Tổng hợp luồng: **Metrics (M3) → Traces (M2) → Logs (M1) → Root cause**.
    *   Dẫn dắt nhóm bàn bạc để đưa ra đề xuất FIX và biện pháp phòng ngừa.

---

### Hoàn tất: Báo cáo và demo (3:30 – 4:00)
**Mục tiêu:** Kiểm tra chéo, dọn dẹp mã nguồn và nộp bài.

*   **M4 (Report & Demo) - Chủ trì:**
    *   Hoàn thiện `submission/REPORT.md` với đầy đủ câu trả lời về root cause, fix, prevention.
    *   Soạn kịch bản Demo theo luồng sự cố vừa điều tra.
*   **M1, M2, M3:**
    *   Kiểm tra code của mình đảm bảo sạch sẽ: Không commit `.env`, không lộ API key.
    *   Chạy test cuối `python -m pytest -q`.
    *   Chạy lại `python scripts/validate_logs.py` để chắc chắn không mất điểm.
    *   Gom toàn bộ code commit lên Git (`git status --short`).
*   **Trưởng nhóm (hoặc M4):** Push repo, lấy URL + commit SHA nộp lên Codelabs.

---

## 📌 Nguyên tắc làm việc nhóm
1. **Lưu vết liên tục:** Bất kỳ ai làm xong task phải chụp ngay screenshot cho M4 lưu vào `evidence/`.
2. **Không tự ý sửa đồ của người khác:** Tránh conflicts khi merge code.
3. **Không hard-code:** Không sửa output tĩnh để đối phó với script chấm điểm.
4. **Không commit bí mật:** Luôn cẩn thận với `.env` và `config/challenge.json` (chỉ dùng bản Lab Coach phát).
