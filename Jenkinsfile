pipeline {
  agent any

  environment {
    AWS_REGION = 'ap-south-1'
    ECR_REPOSITORY = 'royalwheels'
    EKS_CLUSTER = 'royalwheels-dev'
    IMAGE_TAG = "${env.BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Install and Test') {
      steps {
        dir('backend') {
          bat 'python -m pip install --upgrade pip'
          bat 'pip install -r requirements.txt'
          bat 'python manage.py test'
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        bat 'docker build -t %ECR_REPOSITORY%:%IMAGE_TAG% .'
      }
    }

    stage('Push to AWS ECR') {
      steps {
        withCredentials([string(credentialsId: 'aws-account-id', variable: 'AWS_ACCOUNT_ID')]) {
          bat 'aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com'
          bat 'docker tag %ECR_REPOSITORY%:%IMAGE_TAG% %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%:%IMAGE_TAG%'
          bat 'docker tag %ECR_REPOSITORY%:%IMAGE_TAG% %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%:latest'
          bat 'docker push %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%:%IMAGE_TAG%'
          bat 'docker push %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%:latest'
        }
      }
    }

    stage('Deploy to EKS') {
      steps {
        withCredentials([string(credentialsId: 'aws-account-id', variable: 'AWS_ACCOUNT_ID')]) {
          bat 'aws eks update-kubeconfig --region %AWS_REGION% --name %EKS_CLUSTER%'
          bat 'kubectl apply -k k8s/base'
          bat 'kubectl -n royalwheels set image deployment/royalwheels-web web=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%:%IMAGE_TAG%'
          bat 'kubectl -n royalwheels rollout status deployment/royalwheels-web --timeout=180s'
        }
      }
    }
  }

  post {
    always {
      bat 'docker image prune -f'
    }
  }
}
