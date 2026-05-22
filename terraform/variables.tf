variable "project_name" {
  type        = string
  description = "Project name used for AWS resource names."
  default     = "royalwheels"
}

variable "environment" {
  type        = string
  description = "Deployment environment name."
  default     = "dev"
}

variable "aws_region" {
  type        = string
  description = "AWS region for the stack."
  default     = "ap-south-1"
}

variable "db_username" {
  type        = string
  description = "RDS PostgreSQL username."
  default     = "royalwheels"
}

variable "db_password" {
  type        = string
  description = "RDS PostgreSQL password."
  sensitive   = true
}
