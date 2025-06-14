# Terraform AWS Infrastructure Setup

This guide walks you through configuring Terraform to deploy AWS resources.

## Prerequisites

1. **Generate AWS Credentials**  
   Create an Access Key ID and Secret Access Key from the AWS portal.

2. **Configure AWS CLI**  
   Set up your credentials locally using the AWS CLI:

   ```
   aws configure
   ```

   Example prompts:
   ```
   AWS Access Key ID [None]:
   AWS Secret Access Key [None]:
   Default region name [None]: us-east-1
   Default output format [None]: json
   ```

3. **Configure Terraform AWS Provider**  
   The credentials from `aws configure` are used in your `main.tf`:

   ```
   provider "aws" {
     region  = "us-east-1"
     profile = "default"  # Use the profile name from `aws configure`
   }
   ```

## Usage

4. **Initialize and Plan**  
   Run the following commands to initialize and validate your Terraform configuration:

   ```
   terraform init
   terraform plan
   ```

5. **Add Resources**  
   Create additional `.tf` files as needed to define your AWS services.

6. **Production Deployment**  
   For production, use:

   ```
   terraform plan -out=tfplan
   terraform apply "tfplan"
   ```

## Deployment Logs

[12 June 2025] Deploying a DynamoDB table (`dynamo.tf`):

```
PS C:\Users\ulyses.a.solon.jr\Git\foreclosed\infra> terraform apply "tfplan"
aws_dynamodb_table.properties: Creating...
aws_dynamodb_table.properties: Still creating... [00m10s elapsed]
aws_dynamodb_table.properties: Creation complete after 14s [id=properties]
```

[13 June 2025] Deploying a Amplify resource (`amplify.tf`):

```
aws_amplify_app.foreclosed_frontend: Creating...
aws_amplify_app.foreclosed_frontend: Creation complete after 5s [id=d16p20066pnktg]
aws_amplify_branch.foreclosed_frontend_main: Creating...
aws_amplify_branch.foreclosed_frontend_main: Creation complete after 2s [id=d16p20066pnktg/main]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

[14 June 2025] Deploying a Amplify table (`lambda.tf`):

Need to first create the zip of the functions:
```
Compress-Archive -Path .\backend\batch\* -DestinationPath .\infra\batch_lambda.zip -Force
Compress-Archive -Path .\backend\api\* -DestinationPath .\infra\api_lambda.zip -Force
```

Then can do the usual tf plan and tf apply.
```
aws_iam_role.lambda_exec_role: Creating...
aws_iam_role.lambda_exec_role: Creation complete after 3s [id=lambda_exec_role]
aws_iam_role_policy_attachment.lambda_basic_execution: Creating...
aws_lambda_function.api_lambda: Creating...
aws_lambda_function.batch_lambda: Creating...
aws_iam_role_policy_attachment.lambda_basic_execution: Creation complete after 1s [id=lambda_exec_role-20250614101018404400000001]
aws_lambda_function.api_lambda: Still creating... [00m10s elapsed]
aws_lambda_function.batch_lambda: Still creating... [00m10s elapsed]
aws_lambda_function.api_lambda: Creation complete after 13s [id=ApiLambda]
aws_lambda_function.batch_lambda: Still creating... [00m20s elapsed]
aws_lambda_function.batch_lambda: Creation complete after 21s [id=BatchLambda]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.
```