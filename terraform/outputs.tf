output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "eks_cluster_name" {
  value = aws_eks_cluster.main.name
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "database_url_template" {
  value     = "postgres://${var.db_username}:<password>@${aws_db_instance.postgres.address}:5432/royalwheels"
  sensitive = true
}
