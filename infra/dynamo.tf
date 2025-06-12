resource "aws_dynamodb_table" "properties" {
  name         = "properties"
  billing_mode = "PAY_PER_REQUEST"

  hash_key     = "batch_no"
  range_key    = "ropa_id"

  attribute {
    name = "batch_no"
    type = "S"
  }

  attribute {
    name = "ropa_id"
    type = "S"
  }

  tags = {
    Environment = "dev"
    Project     = "foreclosed"
  }
}
