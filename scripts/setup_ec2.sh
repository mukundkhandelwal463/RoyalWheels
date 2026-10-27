#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "      RoyalWheels - AWS EC2 Ubuntu Bootstrap Script       "
echo "=========================================================="

# 1. Update and install prerequisites
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

# 2. Add Docker's official GPG key & repository
sudo install -m 0755 -d /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
fi

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. Install Docker Engine, CLI, and Docker Compose plugin
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. Enable Docker service and add current user to docker group
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER" || true
sudo usermod -aG docker ubuntu || true

# 5. Create deployment directory
mkdir -p /home/ubuntu/royalwheels/nginx
chown -R ubuntu:ubuntu /home/ubuntu/royalwheels || true

echo "=========================================================="
echo " Docker and Docker Compose installed successfully!       "
echo " Deployment directory ready at: /home/ubuntu/royalwheels  "
echo "=========================================================="
