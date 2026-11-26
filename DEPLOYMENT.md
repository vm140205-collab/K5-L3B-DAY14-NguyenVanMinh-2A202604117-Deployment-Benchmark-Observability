# Deployment Information

> **Cần hoàn thành:** deploy agent Part 6 (`06-lab-complete/`) lên Railway hoặc Render, rồi điền URL và chụp ảnh vào `screenshots/`.

## Public URL
<!-- Điền sau khi deploy, ví dụ https://production-agent-production.up.railway.app -->

## Platform
Railway (file cấu hình: `06-lab-complete/railway.toml`) — hoặc Render (`06-lab-complete/render.yaml`)

## Các bước deploy Railway
```bash
npm install -g @railway/cli
railway login
railway init                    # trong thư mục 06-lab-complete/
railway variable set AGENT_API_KEY=$(openssl rand -hex 16)
railway variable set REDIS_URL=<url redis từ Railway Redis plugin>
railway up                      # build từ Dockerfile, healthcheck /health
```

## Test Commands

### Health Check
```bash
curl https://<YOUR-APP>.up.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://<YOUR-APP>.up.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

## Environment Variables Set
- PORT (Railway inject, Dockerfile đọc `$PORT`)
- REDIS_URL
- AGENT_API_KEY (generateValue trong render.yaml / `railway variable set`)
- RATE_LIMIT_PER_MINUTE
- DAILY_BUDGET_USD

## So sánh railway.toml vs render.yaml
| | railway.toml | render.yaml |
|---|---|---|
| Build | `builder = "DOCKERFILE"` | `runtime: docker` |
| Healthcheck | `healthcheckPath = "/health"` + timeout | `healthCheckPath: /health` |
| Secret | `[env]` + required, giá trị set qua CLI/dashboard | `generateValue: true` (Render tự sinh) |
| Redis | thêm plugin/service riêng, lấy `REDIS_URL` | thêm service redis hoặc dùng managed |

## Pipeline Cloud Run (Exercise 3.3)
`03-cloud-deployment/production-cloud-run/` chứa `cloudbuild.yaml` (build image → push Artifact Registry) và `service.yaml` (deploy Cloud Run, scale theo traffic, health check `/health`). Luồng: push code → Cloud Build chạy cloudbuild.yaml → image lên registry → `gcloud run services replace service.yaml` → Cloud Run cấp URL riêng từng revision.

## Screenshots
- [ ] Deployment dashboard — `screenshots/dashboard.png`
- [ ] Service running — `screenshots/running.png`
- [ ] Test results — `screenshots/test.png`
