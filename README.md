# 🚗🏍️ RoyalWheels - Vehicle Rental Management Platform

RoyalWheels is a full-stack vehicle rental platform that enables customers to rent cars and bikes online while providing dedicated dashboards for rental partners and administrators. The platform offers secure authentication, online payments, fleet management, booking tracking, and enterprise-grade deployment infrastructure.

---

## 📌 Project Overview

RoyalWheels streamlines the vehicle rental process by allowing users to:

* Browse available cars and bikes
* Search and filter vehicles
* Book vehicles online
* Manage bookings and profiles
* Make secure online payments
* Access role-based dashboards

The system supports Customers, Rental Partners, and Administrators with dedicated functionalities for each user type.

---

## ✨ Key Features

### Customer Portal

* User Registration & Login
* Google Sign-In Authentication
* OTP Email Verification
* Vehicle Search & Filtering
* Online Vehicle Booking
* Booking History Management
* Responsive User Interface

### Partner Portal

* Fleet Management
* Vehicle Status Updates
* Booking Management
* Revenue Tracking
* Vehicle Listing Controls

### Admin Portal

* User Management
* Vehicle Management
* Booking Monitoring
* Platform Analytics
* System Administration

### Payment Integration

* Razorpay Payment Gateway
* Secure Checkout Process
* Payment Verification

### Cloud Storage

* Cloudinary Integration
* Vehicle Image Upload & Management
* Scalable Media Storage

---

## 🛠️ Technology Stack

### Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap
* Glassmorphism UI Design

### Backend

* Python
* Django Framework

### Database

* PostgreSQL

### Authentication

* Google OAuth
* Email OTP Verification

### Payment Gateway

* Razorpay

### Cloud Storage

* Cloudinary

---

## 🚀 DevOps & Cloud Infrastructure

The project follows modern DevOps practices and includes production-ready deployment configurations.

### Docker

* Dockerfile
* Docker Compose
* Containerized Application Deployment

### Kubernetes

* Deployments
* Services
* Ingress
* Horizontal Pod Autoscaler (HPA)

### Terraform

* AWS VPC
* EKS Cluster
* RDS Database
* ECR Repository

### Jenkins CI/CD

* Automated Build Pipeline
* Automated Testing
* Automated Deployment

### Monitoring & Observability

* Prometheus Metrics Collection
* Grafana Dashboards
* Health Check Endpoints
* Application Monitoring

---

## 📊 System Architecture

GitHub Repository
↓
Jenkins CI/CD Pipeline
↓
Docker Image Build
↓
Amazon ECR
↓
Kubernetes (EKS) Deployment
↓
Application Pods
↓
PostgreSQL Database (RDS)

Monitoring Flow:

Application → Prometheus → Grafana Dashboard

---

## 📈 Monitoring Features

### Prometheus

* Application Metrics
* Request Monitoring
* Resource Utilization
* Service Health Tracking

### Grafana

* Real-Time Dashboards
* CPU & Memory Monitoring
* Request Analytics
* System Health Visualization

---

## 🔧 Running Locally

Clone the repository:

```bash
git clone https://github.com/mukundkhandelwal463/RoyalWheels.git
cd RoyalWheels
```

Start the application:

```bash
docker compose up --build
```

Application URL:

```text
http://localhost:8000
```

Seed Demo Data:

```bash
docker compose exec web python manage.py seed_demo --flush
```

---

## 🔑 Demo Credentials

### Admin

Username: admin
Password: admin123

### Customer

Email: [mukundkhandelwal463@gmail.com](mailto:mukundkhandelwal463@gmail.com)
Password: Demo@123

### Partner

Username: royalwheels_admin
Password: Royal@123

---

## 🌐 Environment Variables

Create a `.env` file and configure:

```env
DJANGO_SECRET_KEY=
DATABASE_URL=
GOOGLE_CLIENT_ID=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
CLOUDINARY_URL=
```

Refer to:

```text
backend/.env.example
```

for sample values.

---

## 🎯 Key Achievements

* Developed a full-stack vehicle rental platform.
* Implemented secure Google OAuth and OTP authentication.
* Integrated Razorpay payment gateway.
* Containerized the application using Docker.
* Automated deployment using Jenkins CI/CD.
* Deployed infrastructure using Terraform on AWS.
* Orchestrated workloads using Kubernetes.
* Implemented monitoring with Prometheus and Grafana.

---

## 👨‍💻 Author

Mukund Khandelwal

GitHub: https://github.com/mukundkhandelwal463
