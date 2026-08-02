# Deployment Guide

This guide covers deploying InternAI to a single VPS (e.g. DigitalOcean, Hetzner, Linode) using Docker Compose and Nginx, plus notes for scaling beyond a single box.

---

## 1. Provision a VPS

Minimum recommended: 2 vCPU, 4GB RAM, 40GB SSD (spaCy + the Python stack are the main memory users; Postgres and Redis are light for moderate traffic).

```bash
ssh root@your-server-ip

apt update && apt upgrade -y
apt install -y docker.io docker-compose-plugin git ufw

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## 2. Clone and configure

```bash
git clone <your-repo-url> /opt/internai
cd /opt/internai

cp backend/.env.example backend/.env
nano backend/.env
```

Set at minimum:
- `SECRET_KEY` — generate with `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
- `ENCRYPTION_KEY` — generate with `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `ENVIRONMENT=production`, `DEBUG=false`
- `BACKEND_CORS_ORIGINS` — your real domain(s)
- `DATABASE_URL` / `DATABASE_URL_SYNC` — leave pointing at the `postgres` service name if using the bundled Compose Postgres, or point at a managed Postgres instance
- SMTP credentials for email notifications
- `TELEGRAM_BOT_TOKEN` if using Telegram notifications
- Storage: either leave `STORAGE_BACKEND=local` (uses a Docker volume) or configure S3/Supabase credentials

## 3. TLS (HTTPS)

The bundled `docker/nginx.conf` serves plain HTTP on port 80. For production, put TLS in front of it. The simplest path is Certbot on the host, terminating TLS before proxying to the Nginx container — or swap in an `nginx-proxy` + `acme-companion` pair. Example using standalone Certbot + a second Nginx layer:

```bash
apt install -y certbot
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

Then update `docker/nginx.conf` to add a `listen 443 ssl;` server block referencing the issued certificate paths (`/etc/letsencrypt/live/yourdomain.com/fullchain.pem` and `privkey.pem`), mount `/etc/letsencrypt` into the Nginx container as a volume, and redirect port 80 to 443. Renew with a cron job or systemd timer calling `certbot renew`.

## 4. Build and launch

```bash
cd /opt/internai
docker compose up -d --build
docker compose logs -f backend   # confirm migrations applied and Uvicorn started
```

Verify:
```bash
curl http://localhost/health
curl http://localhost/api/v1/dashboard/stats   # should 401 without a token — confirms routing works
```

## 5. Database migrations on future deploys

```bash
cd /opt/internai
git pull
docker compose build backend celery_worker celery_beat
docker compose up -d
# The backend container runs `alembic upgrade head` automatically on start (see docker-compose.yml command).
```

To create a new migration after changing models:
```bash
docker compose exec backend alembic revision --autogenerate -m "describe the change"
docker compose exec backend alembic upgrade head
```

## 6. Monitoring the scheduler

Scheduled search runs are logged to the `scheduler_runs` table and exposed via `GET /api/v1/admin/scheduler-runs` (admin-only). To promote a user to admin:

```bash
docker compose exec postgres psql -U internai -d internai \
  -c "UPDATE users SET role = 'admin' WHERE email = 'you@example.com';"
```

Check Celery Beat is actually scheduling tasks:
```bash
docker compose logs -f celery_beat
docker compose logs -f celery_worker
```

## 7. Backups

Postgres data lives in the `postgres_data` named volume. Set up a daily dump:

```bash
# /etc/cron.daily/internai-backup
#!/bin/bash
docker compose -f /opt/internai/docker-compose.yml exec -T postgres \
  pg_dump -U internai internai | gzip > /opt/backups/internai_$(date +%F).sql.gz
find /opt/backups -name "internai_*.sql.gz" -mtime +14 -delete
```

Ship these off-box (S3, rsync to another host, etc.) — a local-only backup doesn't protect against disk failure.

## 8. CI/CD

`.github/workflows/ci.yml` runs tests and builds both Docker images on every push to `main`. To auto-deploy on merge, add a deploy job that SSHes into the VPS and re-runs `docker compose up -d --build` (store the SSH key as a GitHub Actions secret), or push built images to a registry (GHCR/Docker Hub) and have the VPS pull tagged images instead of building on-box.

## Scaling beyond a single VPS

- **Database**: move to a managed Postgres (RDS, Cloud SQL, Supabase) once you outgrow a single-box instance; update `DATABASE_URL`/`DATABASE_URL_SYNC`.
- **Redis**: managed Redis (ElastiCache, Upstash) once Celery throughput grows.
- **Celery workers**: scale horizontally — `docker compose up -d --scale celery_worker=4` on a single box, or run workers on separate machines pointed at the same `CELERY_BROKER_URL`.
- **Storage**: switch `STORAGE_BACKEND=s3` and set the `S3_*` env vars so resumes aren't tied to one host's disk.
- **Frontend**: the Next.js standalone build can be deployed independently (e.g. Vercel) pointed at the backend's public URL via `NEXT_PUBLIC_API_URL`.
