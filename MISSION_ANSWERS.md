# MISSION_ANSWERS — Day 14

> Sinh viên: Nguyễn Văn Minh · MSSV 2A202604117 · Nhóm K5-L3A
> Các con số bên dưới là số đo được trực tiếp trên máy trong buổi lab, không chép từ README.

---

## Part 1 — Localhost vs Production (CP1)

### Exercise 1.1 — Kết quả gọi được bản develop

Chạy: `PYTHONPATH=. python3 -m uvicorn 01-localhost-vs-production.develop.app:app --port 8100`

```
$ curl -X POST "http://localhost:8100/ask?question=hello"
{"answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}
$ curl http://localhost:8100/health
{"detail":"Not Found"}   # HTTP 404 — không có health check
```

### Exercise 1.2 — Ít nhất 5 anti-pattern trong `develop/app.py`

| # | Anti-pattern | Dòng code trong `develop/app.py` | Vì sao nguy hiểm khi production |
|---|---|---|---|
| 1 | API key hardcode trong source | dòng 17: gán thẳng chuỗi key `sk-...` cho `OPENAI_API_KEY` | Push lên GitHub là lộ key; kẻ khác dùng tiền của bạn, phải rotate key + xoá history git |
| 2 | Log secret ra console | dòng 34: `print(f"[DEBUG] Using key: {OPENAI_API_KEY}")` | Secret rò vào log tập trung; ai xem log cũng thấy key |
| 3 | Port cứng | dòng 52: `port=8000` | Vi phạm 12-factor; cloud (Railway/Render) inject PORT riêng, app không chạy được |
| 4 | Không có health check | thiếu hoàn toàn `GET /health` | Orchestrator không biết container sống/chết, không tự restart khi treo |
| 5 | State trong RAM + tắt đột ngột | `uvicorn.run(...)` không xử lý SIGTERM | Scale nhiều instance là mất session; deploy bản mới thì request dở bị cắt |
| 6 | `print()` thay structured logging | toàn bộ file dùng `print` | Log không machine-readable, không gom được về hệ observability |

### Exercise 1.3 — Bảng so sánh develop/production

| Khía cạnh | develop | production | Giải thích |
|---|---|---|---|
| API key | hardcode trong source | đọc từ env qua `config.py` | 12-factor: config nằm trong environment, không trong code |
| Port | cứng `8000` | từ `PORT` env var | Cloud inject PORT tự động |
| State | trong RAM | Redis | Stateless để scale ngang |
| Health check | không có | `GET /health` | Liveness probe cho orchestrator |
| Shutdown | đột ngột | graceful — hoàn thành request hiện tại | Không cắt request người dùng khi deploy |
| Logging | `print()` | structured JSON | Machine-readable, gom về log aggregator được |

---

## Part 2 — Docker (CP2)

### Exercise 2.1 — 4 câu trả lời

**1. Tại sao `COPY requirements.txt .` rồi `RUN pip install` TRƯỚC `COPY . .`?**
Docker cache từng layer. requirements.txt ít đổi nên layer `pip install` được cache; chỉ khi file này đổi mới cài lại. Nếu `COPY . .` đứng trước, sửa một dòng code là phải cài lại toàn bộ package.

**2. `.dockerignore` nên chứa gì?**
`.env`, `venv/`, `.git/`, `__pycache__/`, `*.log`. Quan trọng nhất: `.env` vì secret nằm trong image thì ai có image cũng đọc được; `venv/` vì nó phụ thuộc máy và nặng hàng trăm MB.

**3. Agent cần đọc file từ disk thì mount volume thế nào?**
```yaml
volumes:
  - ./data:/app/data      # bind mount khi dev
  - agent-data:/app/data  # named volume cho production
```
Không `COPY` dữ liệu vào image vì image là bất biến.

**4. Multi-stage giảm dung lượng ở đâu?**
Stage builder chứa pip, build tools, cache cài đặt. Stage cuối chỉ `COPY --from=builder` các package đã cài, không mang compiler/cache. Số đo bên dưới: 236MB so với 1.65GB.

### Exercise 2.2 — Kết quả gọi container

Image build từ gốc repo: `docker build -f 02-docker/develop/Dockerfile -t agent-develop .` và `docker build -f 02-docker/production/Dockerfile -t agent-production .` — cả hai build thành công.

### Exercise 2.3 — Kích thước image (`docker images`)

```
agent-production:latest 236MB
agent-develop:latest 1.65GB
```

Chênh lệch: (1650 − 236) / 1650 ≈ **85.7% nhỏ hơn**.

### Exercise 2.4 — Sơ đồ stack + test qua Nginx

```
client ──▶ nginx :80 ──▶ agent :8000 ──▶ redis :6379
```

```
$ docker compose -p day14-part2 up -d --build
$ curl localhost/health
{"status":"ok","uptime_seconds":1.6,"version":"2.0.0","timestamp":"2026-11-26T07:15:11.235647"}
```

---

## Part 4 — API Security (CP3)

Bản production `04-api-gateway/production`, đo bằng curl:

```
Thiếu key                          → HTTP 401
POST /auth/token (student/demo123) → nhận access_token JWT
/ask với Bearer JWT đúng           → HTTP 200
15 request liên tiếp cùng token:
200 200 200 200 200 200 200 200 200 429 429 429 429 429 429
```

---

## Part 5 — Scaling & Reliability (CP4)

`docker compose -p day14-part5 up -d --build --scale agent=3` → 3 agent + redis + nginx chạy.
`python test_stateless.py` → exit 0: request qua Nginx được phục vụ bởi các instance khác nhau, session vẫn nhất quán nhờ Redis.

Ghi chú: lần chạy đầu lỗi `runc create failed ... cgroup "domain threaded"` do khối `deploy.resources.limits` trong `docker-compose.yml`. Đã bỏ khối đó và stack chạy đủ 3 instance.
