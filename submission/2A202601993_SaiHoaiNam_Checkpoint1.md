# M2 Checkpoint 1 - Tracing & Prompt Version Preparation

## 1. Thong tin ca nhan

- Ho va ten: Sai Hoai Nam
- Ma so sinh vien: 2A202601993
- Role: M2 - Tracing & Prompt Version
- Checkpoint: Checkpoint 1 - Logging va PII

## 2. Muc tieu cua M2 trong Checkpoint 1

Trong Checkpoint 1, M2 khong phai role chu tri Logging va PII. Theo phan chia cong viec, M1 chiu trach nhiem chinh ve correlation ID, JSON logging va PII redaction.

Nhiem vu cua M2 trong checkpoint nay la tim hieu truoc cau truc API de chuan bi gan Langfuse SDK cho checkpoint 2.

Muc tieu cu the:

- Hieu luong xu ly request `/chat`.
- Xac dinh diem phu hop de gan Langfuse tracing.
- Kiem tra logic prompt versioning hien co trong project.
- Nam cac metadata can co tren trace.
- Ghi nhan diem can phoi hop voi M1 de noi trace voi log bang `correlation_id`.

## 3. Luong xu ly request `/chat`

Request chinh cua he thong di qua endpoint `/chat` trong `app/main.py`.

Luong xu ly tong quat:

```text
Client
-> FastAPI endpoint /chat
-> CorrelationIdMiddleware
-> log request_received
-> LabAgent.run()
-> retrieve documents
-> resolve prompt
-> FakeLLM.generate()
-> update Langfuse trace/generation
-> record metrics
-> log response_sent
-> return ChatResponse
```

Cac file lien quan:

- `app/main.py`: dinh nghia endpoint `/chat`, ghi log request/response va goi agent.
- `app/middleware.py`: tao va gan `correlation_id` cho request.
- `app/agent.py`: xu ly RAG, prompt, LLM, metrics va Langfuse trace.
- `app/prompt_management.py`: lay prompt tu Langfuse hoac fallback ve local prompt.
- `app/tracing.py`: adapter Langfuse va dieu kien bat tracing.
- `app/schemas.py`: dinh nghia `ChatRequest`, `ChatResponse` va schema log.

## 4. Diem gan Langfuse tracing

Diem gan trace chinh la ham:

```python
LabAgent.run()
```

trong file `app/agent.py`.

Ham nay da co decorator:

```python
@observe(as_type="generation", capture_input=False, capture_output=False)
```

Day la vi tri phu hop de trace vi toan bo logic AI nam trong ham nay:

- Lay tai lieu bang `retrieve(message)`.
- Lay prompt bang `resolve_prompt(...)`.
- Goi model gia lap bang `FakeLLM.generate(prompt.text)`.
- Tinh `latency_ms`, token, cost va `quality_score`.
- Cap nhat trace va generation len Langfuse.
- Ghi metrics phuc vu dashboard.

## 5. Metadata can co tren trace

Trace can giup nhom biet request da dung user nao, session nao, feature nao, model nao va prompt version nao.

Cac metadata quan trong:

```text
user_id_hash
session_id
feature
model
prompt_name
prompt_label
prompt_version
prompt_source
```

Hien tai trong `app/agent.py`, trace da update cac thong tin:

```text
user_id
session_id
tags
prompt_name
prompt_label
prompt_version
prompt_source
```

Generation cung da ghi them:

- `model`
- `doc_count`
- `query_preview`
- `prompt_name`
- `prompt_label`
- `prompt_version`
- `prompt_source`
- `prompt_fetch_error`
- `prompt_tokens`
- `completion_tokens`
- `cost`

Nhung thong tin nay se duoc dung lam evidence o checkpoint 2 khi chup trace waterfall va prompt version tren Langfuse.

## 6. Prompt versioning

Prompt duoc xu ly trong file `app/prompt_management.py`.

Prompt contract bat buoc:

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
```

App lay prompt dua tren cac bien moi truong:

```dotenv
LANGFUSE_PROMPT_NAME=day13-chat
LANGFUSE_PROMPT_LABEL=production
```

Neu Langfuse kha dung, app se goi `client.get_prompt(...)`, sau do compile prompt voi cac bien:

- `feature`
- `docs`
- `message`

Neu Langfuse khong kha dung hoac fetch prompt bi loi, app se fallback ve local prompt va ghi:

```text
prompt_source=local hoac local-fallback
prompt_version=local-v1
```

Dieu nay giup app van chay duoc khi thieu Langfuse key, nhung khong du evidence trace/prompt version de lay diem toi da cho phan M2.

## 7. Cau hinh Langfuse can kiem tra

M2 can dam bao file `.env` co cac bien sau:

```dotenv
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PROMPT_NAME=day13-chat
LANGFUSE_PROMPT_LABEL=production
```

Trong `app/tracing.py`, tracing chi duoc bat khi co du:

```text
LANGFUSE_PUBLIC_KEY
LANGFUSE_SECRET_KEY
```

Neu thieu mot trong hai key nay, `/health` van tra ve `ok: true`, nhung `tracing_enabled` se la `false`. Khi do app dung local prompt va khong tao duoc evidence trace that tren Langfuse.

## 8. Diem can phoi hop voi M1

Checkpoint 1 do M1 chu tri cac phan:

- Tao va propagate `correlation_id`.
- Ghi JSON log dung schema.
- Bo sung metadata cho log: `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- Redact PII truoc khi ghi log.

M2 can phoi hop voi M1 de dam bao `correlation_id` co the duoc dua vao trace metadata. Dieu nay quan trong cho checkpoint 3 vi nhom can noi duoc luong:

```text
Metrics -> Traces -> Logs -> Root cause
```

Neu trace co `correlation_id`, khi thay mot trace cham hoac loi tren Langfuse, nhom co the tim log tuong ung trong `data/logs.jsonl` de chung minh root cause.

## 9. Chuan bi cho Checkpoint 2

Sau checkpoint 1, M2 can san sang thuc hien cac viec o checkpoint 2:

- Tao prompt `day13-chat` tren Langfuse.
- Tao prompt version 1 va gan labels `baseline`, `production`.
- Tao prompt version 2 va gan label `candidate`.
- Chay cung mot input voi cac label khac nhau.
- Kiem tra trace co `prompt_name`, `prompt_label`, `prompt_version`.
- Thuc hien doi label hoac rollback `production`.
- Chup evidence: trace waterfall, danh sach hai prompt version, trace ID va anh rollback.

## 10. Ket luan Checkpoint 1 cua M2

Trong checkpoint 1, M2 da xac dinh duoc:

- Endpoint chinh can trace la `/chat`.
- Ham xu ly AI chinh la `LabAgent.run()`.
- Prompt duoc quan ly qua `resolve_prompt()`.
- Langfuse duoc cau hinh qua `app/tracing.py`.
- Metadata trace can co de phuc vu checkpoint 2 va checkpoint 3.
- Can phoi hop voi M1 de lien ket trace voi log bang `correlation_id`.

Checkpoint 1 cua M2 hoan thanh khi da hieu ro cau truc API va san sang trien khai trace/prompt version evidence o checkpoint 2.
