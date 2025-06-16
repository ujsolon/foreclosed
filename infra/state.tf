resource "aws_s3_bucket" "foreclosed_tfstate" {
  bucket = "foreclosed-tfstate"

  tags = {
    Environment = "dev"
    Project     = "foreclosed"
  }
}

resource "aws_iam_policy" "github_tf_backend_access" {
  name = "github_tf_backend_access"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ],
        Resource = [
          aws_s3_bucket.foreclosed_tfstate.arn,
          "${aws_s3_bucket.foreclosed_tfstate.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_tf_backend_access" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.github_tf_backend_access.arn
}