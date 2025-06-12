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