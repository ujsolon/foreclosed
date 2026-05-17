# This Terraform configuration defines AWS Lambda functions and their execution roles.
# Lambda access policies are added to the resources terraform files, e.g. s3.tf, dynamo.tf, etc.

resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Effect = "Allow"
      Sid    = ""
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "scraper_lambda" {
  function_name = "ScraperLambda"
  filename      = "${path.module}/scraper_lambda.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"

  source_code_hash = filebase64sha256("${path.module}/scraper_lambda.zip")
  role             = aws_iam_role.lambda_exec_role.arn

  timeout = 180

  environment {
    variables = {
      ENV = "development"
    }
  }

  tags = {
    Environment = "dev"
    Project     = "foreclosed"
  }
}

data "archive_file" "api_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/api"
  output_path = "${path.module}/api_lambda.zip"
}

resource "aws_lambda_function" "api_lambda" {
  function_name = "ApiLambda"
  filename         = data.archive_file.api_zip.output_path
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"

  source_code_hash = data.archive_file.api_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec_role.arn

  environment {
    variables = {
      ENV = "development"
    }
  }

  tags = {
    Environment = "dev"
    Project     = "foreclosed"
  }
}

data "archive_file" "loader_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/loader"
  output_path = "${path.module}/loader_lambda.zip"
}

resource "aws_lambda_function" "loader_lambda" {
  function_name = "LoaderLambda"
  filename         = data.archive_file.loader_zip.output_path
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"

  source_code_hash = data.archive_file.loader_zip.output_base64sha256
  role             = aws_iam_role.lambda_exec_role.arn

  timeout = 180

  environment {
    variables = {
      ENV = "development"
    }
  }

  tags = {
    Environment = "dev"
    Project     = "foreclosed"
  }
}