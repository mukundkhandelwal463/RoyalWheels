# RoyalWheels DevOps Guide

This repo now includes Docker, Kubernetes, Jenkins CI/CD, Terraform infrastructure for AWS, and Prometheus + Grafana monitoring.

## Local Docker stack

```bash
docker compose up --build
```

The Compose stack uses safe local defaults. Keep real secrets in `backend/.env` for local Django runs or in Jenkins/Kubernetes secrets for deployments.

- App: <http://localhost:8000>
- Health: <http://localhost:8000/healthz/>
- Metrics: <http://localhost:8000/metrics>
- Prometheus: <http://localhost:9090>
- Grafana: <http://localhost:3000> with `admin` / `admin`

Grafana provisions `RoyalWheels Overview` automatically with five panels:

1. Request Rate by Method
2. Error Ratio
3. P95 Request Latency
4. Database Query Rate
5. Service Availability

## AWS infrastructure with Terraform

The Terraform stack creates:

- ECR repository for Docker images
- VPC, public/private subnets, NAT, routes
- EKS cluster and managed node group
- Private RDS PostgreSQL database

```bash
cd terraform
terraform init
copy envs\dev\terraform.tfvars.example terraform.tfvars
terraform plan
terraform apply
```

Replace `db_password` before applying. Terraform creates real AWS resources and can create AWS costs.

## Kubernetes deployment

1. Build and push your image to ECR.
2. Replace the image in `k8s/base/deployment.yaml` or let Jenkins set it.
3. Create a real secret from `k8s/base/secret.example.yaml`.
4. Update `k8s/base/configmap.yaml` and `k8s/base/ingress.yaml` with your domain.
5. Deploy:

```bash
kubectl apply -k k8s/base
kubectl apply -f k8s/monitoring/prometheus.yaml
kubectl apply -f k8s/monitoring/grafana.yaml
```

Create the Grafana admin password secret before deploying Grafana:

```bash
kubectl -n royalwheels create secret generic grafana-admin --from-literal=password=change-me
```

## Jenkins CI/CD

`Jenkinsfile` stages:

1. Checkout
2. Install dependencies and run Django tests
3. Build Docker image
4. Push versioned and `latest` tags to AWS ECR
5. Deploy the image to EKS and wait for rollout

Required Jenkins credentials:

- `aws-account-id`: AWS account id as secret text
- AWS credentials configured for the Jenkins agent through environment, instance profile, or Jenkins AWS credentials plugin

Required tools on the Jenkins agent:

- Python
- Docker
- AWS CLI
- kubectl
