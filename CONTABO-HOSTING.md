# Contabo VPS Hosting Guide (Docker)

This guide is for deploying this project to a Contabo Cloud VPS using Docker Compose.

## 1) Recommended VPS Baseline

- OS: Ubuntu 22.04 or 24.04 LTS
- CPU/RAM: minimum 2 vCPU / 4 GB RAM (8 GB recommended)
- Storage: 80+ GB SSD
- Public static IPv4

## 2) DNS and Domain

- Create an `A` record for your domain/subdomain:
  - `app.yourdomain.com -> <VPS_PUBLIC_IP>`
- Wait for DNS propagation before issuing TLS certs.

## 3) Initial Server Hardening

SSH into VPS and run:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl gnupg lsb-release ufw fail2ban git

# Firewall
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Optional but recommended: disable password auth in /etc/ssh/sshd_config
# PasswordAuthentication no
# then: sudo systemctl restart ssh
```

## 4) Install Docker + Compose

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

docker --version
docker compose version
```

## 5) Clone and Configure App

```bash
git clone https://github.com/bizvoguedigital/devopstutor.git
cd devopstutor
```

Create environment files:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with production values:

- `GROQ_API_KEY`
- `JWT_SECRET_KEY` (strong random secret)
- `ENVIRONMENT=production`
- `DEBUG=false`
- `MONGODB_URI` and `MONGODB_DB_NAME` if using external MongoDB

Generate a strong JWT secret:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 6) Reverse Proxy + TLS (Recommended)

Use Nginx (host-level) in front of Docker containers:

- Route `https://app.yourdomain.com` -> frontend container (`5173`)
- Route `/api` -> backend container (`8000`)
- Use Certbot for Let's Encrypt certificates.

High-level Nginx flow:
- listen on 80/443
- terminate TLS
- proxy pass to `http://127.0.0.1:5173`
- for `/api`, proxy pass to `http://127.0.0.1:8000`

## 7) Start Services

```bash
docker compose up -d --build
```

Verify:

```bash
docker compose ps
curl http://localhost:8000/api/health
```

## 8) Update / Redeploy Workflow

```bash
cd ~/devopstutor
git pull origin main
docker compose up -d --build
```

## 9) Backups (Minimum Required)

Set cron jobs for:

- MongoDB dump backup (if self-hosted)
- `backend/uploads` and `backend/sessions` directories
- Store backups off-server (S3, Backblaze, or another VPS)

## 10) Monitoring and Alerts

Minimum setup:

- Uptime monitoring (Uptime Kuma / UptimeRobot)
- Disk/RAM/CPU alerts
- Container restart policy + log rotation

## 11) Security Checklist Before Go-Live

- [ ] `DEBUG=false`
- [ ] `ENVIRONMENT=production`
- [ ] Strong `JWT_SECRET_KEY` configured
- [ ] `.env` files not committed
- [ ] TLS enabled with valid cert
- [ ] SSH key-only login enabled
- [ ] Firewall active (`ufw`)
- [ ] Backup job validated

## 12) Rollback Strategy

- Keep last known-good image tags or previous commit hash.
- If deploy fails:
  1. `git checkout <last_good_commit>`
  2. `docker compose up -d --build`

---

## Immediate Priority (Contabo)

1. Provision VPS + secure SSH/firewall.
2. Deploy current app with Docker Compose.
3. Add TLS reverse proxy (Nginx + Let's Encrypt).
4. Complete authentication hardening tasks (`AUTHENTICATION-TASKS.md`).
5. Add CI pipeline and controlled deployment workflow.
