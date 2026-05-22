# RoyalWheels 🚗🏍️

RoyalWheels is a comprehensive vehicle rental management platform (Cars & Bikes) built with **Django** on the backend and modern vanilla HTML/CSS/JS for the frontend.

## Key Features
- **Customer Portal**: Book vehicles, manage profiles, multi-login support (Google Sign-In + OTP Email verification).
- **Beautiful UI/UX**: Custom glassmorphism popups, stunning vehicle cards, dynamic search.
- **Admin & Partner Portals**: Rental agencies can manage their own fleet, handle bookings, track revenue, and update vehicle status.
- **Payment Gateway**: Integrated with Razorpay for secure checkout flows.
- **Cloud Storage**: Cloudinary integration for scalable vehicle image storage.

## DevOps & Cloud Infrastructure
This project is fully containerized and includes a comprehensive DevOps scaffold for enterprise-grade deployment:
- **Docker**: Ready-to-go `docker-compose.yml` and `Dockerfile`.
- **Kubernetes**: Standard manifests in `k8s/` for Deployments, Services, Ingress, and HPAs.
- **Terraform**: AWS infrastructure as code in `terraform/` (EKS, RDS, VPC, ECR).
- **Jenkins**: CI/CD pipeline defined in `Jenkinsfile`.
- **Observability**: Prometheus metrics endpoint (`/metrics`), `/healthz/` endpoint, and Grafana dashboards (`grafana/dashboards/royalwheels-overview.json`).
- **Render**: Included `render.yaml` blueprint for one-click PaaS deployment.

See `docs-devops.md` for deep-dive setup and deployment instructions for AWS and Kubernetes.

## Running Locally

To spin up the entire application along with PostgreSQL and Prometheus:

```bash
docker compose up --build
```
This maps the application to `http://localhost:8000`.

To seed the demo data:
```bash
docker compose exec web python manage.py seed_demo --flush
```

Demo Credentials:
- **Admin**: admin / admin123
- **Customer**: mukundkhandelwal463@gmail.com / Demo@123
- **Partner**: royalwheels_admin / Royal@123

## Environment Variables

For full functionality, ensure the following environment variables are set (either in a `.env` file or in your platform secrets manager):

- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `GOOGLE_CLIENT_ID`
- `RAZORPAY_KEY_ID` & `RAZORPAY_KEY_SECRET`
- `EMAIL_HOST_USER` & `EMAIL_HOST_PASSWORD` (for OTP)
- `CLOUDINARY_URL` (for image uploads)

*(See `backend/.env.example` for placeholders).*
