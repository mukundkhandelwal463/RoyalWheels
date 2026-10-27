# RoyalWheels 🚗 — Complete AWS EC2 & GitHub Actions CI/CD Deployment Guide

This guide walks you through deploying **RoyalWheels** to **AWS EC2 (Europe Stockholm - eu-north-1)** with a fully automated **GitHub Actions CI/CD Pipeline**.

---

## 🏗️ Architecture Overview

```text
[ Developer / Git Push ]
           │
           ▼
[ GitHub Repository: RoyalWheels ]
           │  (Push to master / main)
           ▼
[ GitHub Actions Workflow (.github/workflows/deploy.yml) ]
    ├─ 1. Run Django Automated Test Suite (app/tests.py)
    ├─ 2. Build Docker Container
    ├─ 3. Push Image to GitHub Container Registry (ghcr.io)
    └─ 4. Deploy to AWS EC2 via SSH:
           ├─ Copy docker-compose.prod.yml & nginx/
           ├─ Pull latest image from ghcr.io
           ├─ Launch containers (web, db, nginx)
           ├─ Run migrations (`manage.py migrate`)
           ├─ Collect static assets (`manage.py collectstatic`)
           └─ Verify Health Check at `/healthz/` (200 OK)
           │
           ▼
[ AWS EC2 Instance (Stockholm eu-north-1) ]
    ├── Nginx (Port 80 / 443)  --> Reverse Proxy
    ├── Django Gunicorn (Port 8000)
    └── PostgreSQL 16 (Port 5432)
```

---

## 🚀 Step 1: Launch your EC2 Instance in AWS (eu-north-1)

Choose **Method A** (2-minute AWS Console) or **Method B** (Terraform):

### Method A: AWS Console (Recommended — matches your active browser screen)

1. Open your AWS EC2 Console in Europe Stockholm (`eu-north-1`):
   👉 [https://eu-north-1.console.aws.amazon.com/ec2/home?region=eu-north-1#Instances:](https://eu-north-1.console.aws.amazon.com/ec2/home?region=eu-north-1#Instances:)
2. Click **Launch instances** (orange button).
3. Configure the following:
   - **Name**: `royalwheels-prod`
   - **Application and OS Images**: Select **Ubuntu** (Ubuntu Server 24.04 LTS or 22.04 LTS, 64-bit x86).
   - **Instance type**: `t3.small` (Recommended: 2 vCPU, 2GB RAM — smooth Docker builds) or `t3.micro` (Free-tier eligible: 1GB RAM).
   - **Key pair (login)**: Select **`ubuntu-key`** (you already have `ubuntu-key.pem` in `Downloads/`) or create a new key pair (.pem) and download it.
   - **Network settings**:
     - Check **Allow SSH traffic from anywhere (0.0.0.0/0)**
     - Check **Allow HTTP traffic from the internet**
     - Check **Allow HTTPS traffic from the internet**
     - Click **Edit** -> Add another security group rule:
       - Type: **Custom TCP**
       - Port range: `8000`
       - Source: `0.0.0.0/0`
   - **Configure storage**: 20 GiB or 25 GiB (gp3).
   - **Advanced details** (scroll to the bottom):
     In the **User data** box, paste this bootstrap script to install Docker automatically:

```bash
#!/bin/bash
set -e
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release git

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

mkdir -p /home/ubuntu/royalwheels/nginx
chown -R ubuntu:ubuntu /home/ubuntu/royalwheels
```

4. Click **Launch instance**!
5. After 30 seconds, copy the **Public IPv4 address** of your instance (e.g., `13.53.xxx.xxx`).

---

### Method B: Terraform (Alternative)

If you have valid AWS credentials configured:
```bash
cd terraform/ec2
terraform init
terraform apply -auto-approve
```
Terraform will output your EC2 public IP and SSH command automatically!

---

## 🔑 Step 2: Configure GitHub Repository Secrets

The GitHub Actions workflow requires 3 secrets to connect to your EC2 instance:

1. Go to your GitHub repository:
   👉 **[https://github.com/mukundkhandelwal463/RoyalWheels/settings/secrets/actions](https://github.com/mukundkhandelwal463/RoyalWheels/settings/secrets/actions)**
2. Click **New repository secret** and add the following 3 secrets:

| Secret Name | Value | Example / Description |
| :--- | :--- | :--- |
| **`EC2_HOST`** | Your EC2 Public IPv4 | `13.53.120.45` |
| **`EC2_USER`** | `ubuntu` | Default Ubuntu username |
| **`EC2_SSH_KEY`** | Complete content of your `.pem` key file | Open `C:\Users\Mukund\Downloads\ubuntu-key.pem` with Notepad, copy everything including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----` |

*(Optional Secrets: You can also optionally add `DJANGO_SECRET_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `CLOUDINARY_URL`, etc., or let the default production values in the pipeline take effect).*

---

## ⚡ Step 3: Trigger the Automated Deployment

All workflow files, Docker compose configurations, and Nginx settings are now committed and ready.

Simply push your code to GitHub:

```bash
git add .
git commit -m "feat: complete CI/CD automated deployment to AWS EC2 via GitHub Actions"
git push origin master
```

### What happens automatically:
1. GitHub Actions detects the push and triggers **CI/CD Pipeline - Test, Build & Deploy to AWS EC2**.
2. **Job 1 (Test)**: Runs Django unit tests and ensures no bugs exist.
3. **Job 2 (Build & Push)**: Packages your application into a production Docker image and publishes to GitHub Container Registry (`ghcr.io/mukundkhandelwal463/royalwheels:latest`).
4. **Job 3 (Deploy)**: SSHs into your EC2 server, updates Docker Compose, pulls the fresh image, runs migrations, collects static assets, and boots up the services!
5. **Healthcheck**: Verifies `http://<YOUR_EC2_IP>/healthz/` returns `{"status":"ok"}`.

---

## 🌐 Step 4: Access Your Live Application

Once the GitHub Actions workflow finishes with a green checkmark (usually ~2-3 minutes), visit:

- **Web Application**: `http://<YOUR_EC2_IP>`
- **Direct Django Port**: `http://<YOUR_EC2_IP>:8000`
- **Health Check**: `http://<YOUR_EC2_IP>/healthz/`
- **Django Admin**: `http://<YOUR_EC2_IP>/admin/`

To seed demo data (cars, bikes, partners) on the server at any time:
```bash
ssh -i C:/Users/Mukund/Downloads/ubuntu-key.pem ubuntu@<YOUR_EC2_IP>
cd /home/ubuntu/royalwheels
docker compose -f docker-compose.prod.yml exec web python manage.py seed_demo
```

---

## 🛠️ Handy Commands on the EC2 Server

```bash
# SSH into EC2
ssh -i C:/Users/Mukund/Downloads/ubuntu-key.pem ubuntu@<YOUR_EC2_IP>

# Check running containers
docker compose -f /home/ubuntu/royalwheels/docker-compose.prod.yml ps

# View live application logs
docker compose -f /home/ubuntu/royalwheels/docker-compose.prod.yml logs -f web

# Restart all services
docker compose -f /home/ubuntu/royalwheels/docker-compose.prod.yml restart
```
