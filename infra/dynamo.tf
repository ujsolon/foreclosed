resource "aws_dynamodb_table" "properties" {
  name         = "properties"
  billing_mode = "PAY_PER_REQUEST"

  hash_key     = "source_property_id"

  attribute {
    name = "source_property_id"
    type = "S"
  }

  tags = {
    Environment = "dev"
    Project     = "foreclosed"
  }
}

resource "aws_iam_policy" "lambda_dynamodb_access_policy" {
  name = "lambda_dynamodb_access_policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ],
        Resource = "arn:aws:dynamodb:us-east-1:*:table/properties"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_dynamodb_access_policy" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_dynamodb_access_policy.arn
}
