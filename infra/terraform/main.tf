terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "javagar-devsecops"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ── Variables ──────────────────────────────────────────────────────
variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

# ── ECR Repository ────────────────────────────────────────────────
resource "aws_ecr_repository" "javagar_app" {
  name                 = "javagar-app"
  image_tag_mutability = "IMMUTABLE"   # Phase 3: tag immutability

  image_scanning_configuration {
    scan_on_push = true   # Phase 3: scan on push
  }

  encryption_configuration {
    encryption_type = "KMS"
  }
}

# ── ECR Lifecycle Policy ──────────────────────────────────────────
resource "aws_ecr_lifecycle_policy" "javagar_app" {
  repository = aws_ecr_repository.javagar_app.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# ── Outputs ───────────────────────────────────────────────────────
output "ecr_repository_url" {
  value = aws_ecr_repository.javagar_app.repository_url
}
