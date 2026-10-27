variable "aws_region" {
  type        = string
  description = "AWS region for deployment"
  default     = "ap-south-1"
}

variable "project_name" {
  type        = string
  description = "Project name"
  default     = "royalwheels"
}

variable "instance_type" {
  type        = string
  description = "EC2 Instance type (t3.micro is free-tier eligible, t3.small recommended for 2GB RAM)"
  default     = "t3.small"
}

variable "key_name" {
  type        = string
  description = "Name of existing AWS EC2 Key Pair (e.g. ubuntu-key)"
  default     = "ubuntu-key"
}
