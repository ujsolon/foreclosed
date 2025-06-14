# Re-architecting to use S3 and CloudFront instead of Amplify for the frontend deployment.
# resource "aws_amplify_app" "foreclosed_frontend" {
#   name       = "foreclosed_frontend"
#   repository = "https://github.com/ujsolon/foreclosed"
#   oauth_token = var.github_token

#   # Point to where the amplify.yml file is LOCALLY during terraform apply
#   build_spec = file("../frontend/amplify.yml")  # if it's one dir above infra/

#   environment_variables = {
#     ENVIRONMENT = "dev"
#   }

#   platform = "WEB_COMPUTE"
# }


# resource "aws_amplify_branch" "foreclosed_frontend_main" {
#   app_id      = aws_amplify_app.foreclosed_frontend.id
#   branch_name = "main"  # or whatever branch you want to auto-deploy

#   stage = "DEVELOPMENT"

#   environment_variables = {
#     NODE_ENV = "development"
#   }

#   enable_auto_build = true
# }
