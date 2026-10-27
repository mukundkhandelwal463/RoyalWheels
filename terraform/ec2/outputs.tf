output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.app_server.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = aws_instance.app_server.public_dns
}

output "ssh_connection_command" {
  description = "Command to SSH into the EC2 instance"
  value       = "ssh -i C:/Users/Mukund/Downloads/${var.key_name}.pem ubuntu@${aws_instance.app_server.public_ip}"
}

output "web_url" {
  description = "Web Application URL"
  value       = "http://${aws_instance.app_server.public_ip}"
}

output "github_secrets_required" {
  description = "GitHub Repository Secrets to configure"
  value = {
    EC2_HOST    = aws_instance.app_server.public_ip
    EC2_USER    = "ubuntu"
    EC2_SSH_KEY = "Contents of your .pem file (e.g. C:/Users/Mukund/Downloads/${var.key_name}.pem)"
  }
}
