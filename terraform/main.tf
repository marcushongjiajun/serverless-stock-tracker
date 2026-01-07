# 1. SNS Topic for Email alerts
resource "aws_sns_topic" "stock_alerts" {
    name = "daily-stock-analysis-alerts"
}

resource "aws_sns_topic_subscription" "email_target" {
  topic_arn = aws_sns_topic.stock_alerts.arn
  protocol = "email"
  endpoint = "hongjiajun95@gmail.com"
}

# 2. IAM Role to allow Lambda to talk to AWS services
resource "aws_iam_role" "lambda_role" {
  name = "stock_analyst_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# 2a. Attach permission to write logs to CloudWatch
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# 2b. Custom policy to allow publishing to my SNS topic only (Least Privilege)
resource "aws_iam_role_policy" "sns_publish" {
  name = "sns_publish_policy"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
        Effect = "Allow"
        Action = "sns:Publish"
        Resource = aws_sns_topic.stock_alerts.arn
    }]
  })
}

# 3. Lambda Function
resource "aws_lambda_function" "stock_analyst" {
  function_name = "stock-analyst-function"
  role = aws_iam_role.lambda_role.arn
  package_type = "Image"
  image_uri = "${aws_ecr_repository.stock_analyst.repository_url}:latest"

  timeout = 30
  memory_size = 512

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.stock_alerts.arn
    }
  }
}

# 4. Trigger: EventBridge to trigger daily
resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name = "stock-analysis-daily-trigger"
  schedule_expression = "cron(0 1 ? * MON-FRI *)" # Runs 9AM SGT / 1AM UTC
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "StockAnalystLambda"
  arn = aws_lambda_function.stock_analyst.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id = "AllowsExecutionFromEventBridge"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stock_analyst.function_name
  principal = "events.amazonaws.com"
  source_arn = aws_cloudwatch_event_rule.daily_trigger.arn
}

# 5. Set CloudWatch retention policy to 3 days (Cost Savings)
resource "aws_cloudwatch_log_group" "stock_analyst_logs" {
  # AWS Lambda automatically creates a log group at /aws/lambda/<function_name>
  name = "/aws/lambda/stock-analyst-function"
  retention_in_days = 3
}