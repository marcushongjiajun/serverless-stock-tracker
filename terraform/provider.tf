# Global settings

terraform {
  # Run code on HCP Terraform
  cloud {
    organization = "mh-terraform-learn"
    workspaces {
      name    = "stock-analyst"
      project = "Stock Analyst"
    }
  }
  required_providers {
    aws = {
      # version constraints, to avoid major version upgrades during normal operations
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
  # Terraform version
  required_version = "~> 1.2"
}

# Provider
provider "aws" {
  region = "ap-southeast-1"
}