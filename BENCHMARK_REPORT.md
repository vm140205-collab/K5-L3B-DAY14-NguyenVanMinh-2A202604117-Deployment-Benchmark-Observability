# BENCHMARK_REPORT — Day 14

> Sinh viên: Nguyễn Văn Minh · MSSV 2A202604117 · Nhóm K5-L3A
> Số liệu đo trực tiếp trên máy lab (Docker 29.1.3, 4 CPU), agent benchmark chạy bằng `uvicorn` một worker.

## 1. Hiệu năng (`load_test.py`, agent v2, port 8002)

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO p95 ≤ 500ms |
|---|---|---|---|---|---|---|
| 1 | 4.3 | 194.4 | 227.6 | 1677.7 | 0.50% | ✅ |
| 20 (300 req) | 65.2 | 168.7 | 202.0 | 1685.0 | 1.33% | ✅ |
| 50 | 43.0 | 349.0 | 2796.4 | 2938.8 | 1.00% | ❌ |
| 100 | 41.9 | 765.6 | 2916.7 | 3351.2 | 0.00% | ❌ |

**Nhận xét:** với 1 worker uvicorn, thông lượng bão hoà ~42–65 req/s; từ concurrency 50 trở lên p95 vượt SLO 500ms → cần scale ngang (thêm worker/instance) chứ không tăng concurrency client. p99 luôn ~1.7s ở mọi mức → tail latency đến từ request mock LLM chậm bất thường (MOCK_SLOW_RATE mặc định 3%), không phải từ tổng thể hệ thống.

## 2. Tail latency — ảnh hưởng của request chậm (MOCK_SLOW_RATE)

| MOCK_SLOW_RATE | avg (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|
| 0 | 247.7 | 266.1 | 1688.9 |
| 0.03 | 260.1 | 1691.8 | 1718.0 |
| 0.1 | 227.1 | 273.4 | 1693.3 |

**Nhận xét:** chỉ **p95** nhạy nhất với request chậm — chỉ 3% request chậm đã đẩy p95 từ ~270ms lên ~1.7s, trong khi avg gần như đứng yên. Vì vậy SLO phải đặt theo percentile (p95/p99), không theo average: average che giấu trải nghiệm của nhóm người dùng xấu nhất.

## 3. Chi phí LLM

Từ eval report: tổng cost **$0.00076** cho 23 câu, trung bình ~**$0.000036/câu đúng** (mock gpt-4o-mini pricing). Với DAILY_BUDGET_USD = $1 → đủ cho ~27.000 câu/ngày trước khi cost guard trả 402.

## 4. Chất lượng (`eval/run_eval.py` trên golden dataset 23 câu)

| Chỉ số | v1 (baseline) | v2 (hiện tại) | Thay đổi |
|---|---|---|---|
| Accuracy | 91.3% (21/23) | 91.3% (21/23) | +0.0 |
| Latency p95 (ms) | 217.3 | 206.9 | −10.4 |
| Avg tokens/câu | 109.0 | 108.8 | −0.2 |
| Tổng cost (USD) | 0.000760 | 0.000758 | −0.000002 |
| Quality gate (≥80%, không regression) | ✅ PASS | ✅ PASS | — |

Câu yếu của cả hai version: category `scaling` (2/3) và `security` (1/2) trong v1 — mock LLM trả lời khái quát nên những câu đòi chi tiết triển khai không khớp hoàn toàn.

## 5. Reliability — kết quả demo error/fallback

| Kịch bản | MOCK_ERROR_RATE | Kết quả |
|---|---|---|
| Bình thường | 0 | error 0.00%, 200/200 |
| Lỗi ngẫu nhiên LLM | 0.2 | agent trả 503 một phần — cần retry/fallback ở tầng client |

## 6. Kết luận & đề xuất

- Agent v2 đạt quality gate, không regression so với v1 → được phép deploy.
- SLO khuyến nghị: p95 ≤ 500ms, error ≤ 2% ở concurrency ≤ 20 mỗi instance; vượt ngưỡng thì scale ngang.
- Theo dõi qua metrics `/metrics` (Prometheus): `http_request_duration_seconds_bucket`, `llm_cost_usd_total`.

## Files đính kèm
- `06-lab-complete/reports/eval_v1.json` — baseline eval
- `06-lab-complete/reports/eval_v2.json` — eval v2 + so sánh
- `06-lab-complete/reports/load_test_v2.log` — load test 300 req / concurrency 20
