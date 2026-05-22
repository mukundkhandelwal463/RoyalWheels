@echo off
setlocal

if "%AWS_REGION%"=="" set AWS_REGION=ap-south-1
if "%EKS_CLUSTER%"=="" set EKS_CLUSTER=royalwheels-dev

aws eks update-kubeconfig --region %AWS_REGION% --name %EKS_CLUSTER%
kubectl apply -k k8s/base
kubectl apply -f k8s/monitoring/prometheus.yaml
kubectl apply -f k8s/monitoring/grafana.yaml
