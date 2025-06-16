provider "aws" {
  region  = "us-east-1"
  # profile = "default"  # use the same name you used in `aws configure`
}

terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Comment this out if you want to use local for state management
terraform {
  backend "s3" {
    bucket  = "foreclosed-tfstate"
    key     = "terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
