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


resource "aws_lambda_function" "api_lambda" {
  function_name = "ApiLambda"
  filename      = "${path.module}/api_lambda.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"

  source_code_hash = filebase64sha256("${path.module}/api_lambda.zip")
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
