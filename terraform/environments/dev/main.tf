terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
   backend "s3" {
    bucket         = "my-terraform-state-automation-platform-bucket"
    key            = "dev/terraform.tfstate"
    region         = "ap-south-1"
    use_lockfile   = true 
    encrypt        = true
  }
}

provider "aws" {
  region = "ap-south-1"
} 


module "vpc" {
  source = "../../modules/vpc"

  project_name         = "automation-platform"
  environment          = "dev"
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.3.0/24", "10.0.4.0/24"]
  availability_zones   = ["ap-south-1a", "ap-south-1b"]
}

module "eks" {
  source = "../../modules/eks"

  project_name       = "automation-platform"
  environment        = "dev"
  private_subnet_ids = module.vpc.private_subnet_ids
  vpc_id             = module.vpc.vpc_id
}


module "ecr" {
  source = "../../modules/ecr"

  project_name = "automation-platform"
  environment  = "dev"
}
