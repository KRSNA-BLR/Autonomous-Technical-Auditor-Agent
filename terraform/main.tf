# =============================================================================
# Terraform Configuration - AWS Deployment
# =============================================================================
# This Terraform configuration deploys the Research Agent to AWS App Runner,
# providing a serverless, auto-scaling container deployment.
#
# Prerequisites:
#   - AWS CLI configured with appropriate credentials
#   - Terraform installed (v1.0+)
#   - Docker image pushed to ECR
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply
# =============================================================================

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment for remote state storage (recommended for production)
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "research-agent/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# -----------------------------------------------------------------------------
# Provider Configuration
# -----------------------------------------------------------------------------

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "autonomous-tech-research-agent"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "your-name"
    }
  }
}

# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "research-agent"
}

variable "groq_api_key" {
  description = "Groq API key (stored securely)"
  type        = string
  sensitive   = true
}

variable "llm_model" {
  description = "LLM model to use"
  type        = string
  default     = "llama-3.3-70b-versatile"
}

# -----------------------------------------------------------------------------
# ECR Repository - Container Registry
# -----------------------------------------------------------------------------

resource "aws_ecr_repository" "research_agent" {
  name                 = "${var.app_name}-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.app_name}-ecr"
  }
}

# Lifecycle policy to clean up old images
resource "aws_ecr_lifecycle_policy" "research_agent" {
  repository = aws_ecr_repository.research_agent.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# IAM Role - App Runner Access
# -----------------------------------------------------------------------------

resource "aws_iam_role" "apprunner_access_role" {
  name = "${var.app_name}-apprunner-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_access" {
  role       = aws_iam_role.apprunner_access_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# -----------------------------------------------------------------------------
# IAM Role - App Runner Instance
# -----------------------------------------------------------------------------

resource "aws_iam_role" "apprunner_instance_role" {
  name = "${var.app_name}-apprunner-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# App Runner Service
# -----------------------------------------------------------------------------

resource "aws_apprunner_service" "research_agent" {
  service_name = "${var.app_name}-${var.environment}"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access_role.arn
    }

    image_repository {
      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          GROQ_API_KEY            = var.groq_api_key
          LLM_MODEL               = var.llm_model
          API_HOST                = "0.0.0.0"
          API_PORT                = "8000"
          API_DEBUG               = var.environment == "dev" ? "true" : "false"
          LOG_LEVEL               = var.environment == "prod" ? "INFO" : "DEBUG"
          AGENT_MAX_ITERATIONS    = "10"
          AGENT_MEMORY_SIZE       = "20"
        }
      }
      image_identifier      = "${aws_ecr_repository.research_agent.repository_url}:latest"
      image_repository_type = "ECR"
    }

    auto_deployments_enabled = true
  }

  instance_configuration {
    cpu               = "1024"  # 1 vCPU
    memory            = "2048"  # 2 GB
    instance_role_arn = aws_iam_role.apprunner_instance_role.arn
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.research_agent.arn

  tags = {
    Name = "${var.app_name}-service"
  }
}

# -----------------------------------------------------------------------------
# Auto Scaling Configuration
# -----------------------------------------------------------------------------

resource "aws_apprunner_auto_scaling_configuration_version" "research_agent" {
  auto_scaling_configuration_name = "${var.app_name}-autoscaling"

  max_concurrency = 100
  max_size        = 5
  min_size        = 1

  tags = {
    Name = "${var.app_name}-autoscaling"
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.research_agent.repository_url
}

output "app_runner_service_url" {
  description = "App Runner service URL"
  value       = aws_apprunner_service.research_agent.service_url
}

output "app_runner_service_arn" {
  description = "App Runner service ARN"
  value       = aws_apprunner_service.research_agent.arn
}

output "deployment_instructions" {
  description = "Instructions to deploy a new version"
  value       = <<-EOT
    
    🚀 Deployment Instructions:
    
    1. Build and push Docker image:
       aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.research_agent.repository_url}
       docker build -t ${var.app_name} .
       docker tag ${var.app_name}:latest ${aws_ecr_repository.research_agent.repository_url}:latest
       docker push ${aws_ecr_repository.research_agent.repository_url}:latest
    
    2. App Runner will automatically deploy the new image!
    
    3. Access your API at: https://${aws_apprunner_service.research_agent.service_url}
    
  EOT
}
