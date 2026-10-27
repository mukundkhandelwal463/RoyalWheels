pipeline {
  agent any

  environment {
    EC2_HOST = '16.4.56.220'
    EC2_USER = 'ubuntu'
    SSH_KEY = '/var/jenkins_home/.ssh/royalwheels-key.pem'
    IMAGE_NAME = 'royalwheels:prod'
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
            python3 -m venv venv || true
            . venv/bin/activate
            python3 -m pip install --upgrade pip
            pip3 install -r requirements.txt
            DJANGO_SECRET_KEY="test" DJANGO_DEBUG="True" python3 manage.py test app
          '''
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        sh "docker build -t ${IMAGE_NAME} ."
      }
    }

    stage('Deploy to EC2') {
      steps {
        sh '''
          echo "Syncing configs to EC2..."
          scp -i ${SSH_KEY} -o StrictHostKeyChecking=no docker-compose.prod.yml ${EC2_USER}@${EC2_HOST}:/home/ubuntu/royalwheels/docker-compose.prod.yml
          scp -i ${SSH_KEY} -o StrictHostKeyChecking=no nginx/nginx.conf ${EC2_USER}@${EC2_HOST}:/home/ubuntu/royalwheels/nginx/nginx.conf

          echo "Deploying on EC2..."
          ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} """
            set -e
            cd /home/ubuntu/royalwheels/repo
            git fetch origin master
            git reset --hard origin/master
            docker build -t royalwheels:prod /home/ubuntu/royalwheels/repo
            cd /home/ubuntu/royalwheels
            APP_IMAGE=royalwheels:prod docker compose -f docker-compose.prod.yml up -d --remove-orphans
            docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput
            docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
            docker image prune -f
          """

          echo "Verifying Health Check on http://${EC2_HOST}/healthz/..."
          curl --retry 5 --retry-delay 5 --retry-connrefused -f "http://${EC2_HOST}/healthz/"
          echo "RoyalWheels deployed to EC2 successfully via Jenkins!"
        '''
      }
    }
  }

  post {
    always {
      sh 'docker image prune -f'
    }
  }
}
