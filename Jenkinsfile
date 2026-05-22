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
          sh '''
            python3 -m venv venv
            . venv/bin/activate
            python3 -m pip install --upgrade pip
            pip3 install -r requirements.txt
            python3 manage.py test
          '''
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        sh "docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} ."
      }
    }

    stage('Push to AWS ECR') {
      steps {
        withCredentials([string(credentialsId: 'aws-account-id', variable: 'AWS_ACCOUNT_ID')]) {
          sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
          sh "docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
          sh "docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest"
          sh "docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
          sh "docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:latest"
        }
      }
    }

    stage('Deploy to EKS') {
      steps {
        withCredentials([string(credentialsId: 'aws-account-id', variable: 'AWS_ACCOUNT_ID')]) {
          sh "aws eks update-kubeconfig --region ${AWS_REGION} --name ${EKS_CLUSTER}"
          sh 'kubectl apply -k k8s/base'
          sh "kubectl -n royalwheels set image deployment/royalwheels-web web=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"
          sh 'kubectl -n royalwheels rollout status deployment/royalwheels-web --timeout=180s'
        }
      }
    }
  }

  post {
    always {
      sh 'docker image prune -f'
    }
  }
}
