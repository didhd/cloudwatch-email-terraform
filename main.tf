provider "aws" {
  region = "ap-northeast-2"
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "lambda_policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "cloudwatch:GetDashboard",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
    ]
  })
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "lambda/"
  output_path = "lambda.zip"
}

resource "aws_lambda_function" "dashboard_snapshot" {
  function_name = "DashboardSnapshot"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = filebase64sha256(data.archive_file.lambda_zip.output_path)
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.8"
  role             = aws_iam_role.lambda_execution_role.arn

  timeout = 60

  environment {
    variables = {
      DASHBOARD_NAME   = var.dashboard_name
      SENDER_EMAIL     = var.sender_email
      RECIPIENT_EMAILS = join(",", var.recipient_emails)
    }
  }
}

resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "daily-dashboard-snapshot"
  description         = "Trigger Lambda daily for dashboard snapshot"
  schedule_expression = var.cron # Every day at 00:00 UTC
}

resource "aws_cloudwatch_event_target" "invoke_lambda_daily" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "DashboardSnapshot"
  arn       = aws_lambda_function.dashboard_snapshot.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_snapshot" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dashboard_snapshot.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
}

resource "aws_iam_policy" "lambda_ses_policy" {
  name        = "lambda_ses_policy"
  description = "IAM policy for SES email sending from Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail", ]
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_ses_policy_attach" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_ses_policy.arn
}

resource "aws_iam_policy" "lambda_cloudwatch_policy" {
  name        = "lambda_cloudwatch_policy"
  description = "IAM policy for invoking CloudWatch from Lambda"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "cloudwatch:GetMetricWidgetImage",
          "cloudwatch:GetDashboard", // 이미 있는 권한을 유지합니다.
          // 필요한 다른 CloudWatch 관련 권한을 추가하세요.
        ],
        Resource = "*" // 필요에 따라 더 구체적인 리소스 ARN으로 제한할 수 있습니다.
      },
      // 기존 IAM 정책 구성 요소를 유지합니다.
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_policy_attach" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_cloudwatch_policy.arn
}

resource "aws_ses_email_identity" "sender" {
  email = var.sender_email
}

resource "aws_ses_email_identity" "recipients" {
  for_each = toset(var.recipient_emails)

  email = each.value
}
