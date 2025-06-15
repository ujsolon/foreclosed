variable "github_token" {
  description = "GitHub OAuth token for Amplify"
  type        = string
  sensitive   = true
}

variable "lambda_package" {
  type = string
}