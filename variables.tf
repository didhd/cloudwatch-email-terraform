variable "dashboard_name" {
  description = "Name of the CloudWatch Dashboard"
  type        = string
  default     = "Datanode_yICsFgP5SL2KGN-1-uO2jQ_anycommerce-logging"
}

variable "sender_email" {
  description = "Email address of the sender"
  type        = string
  default     = "sanghwa@amazon.com"
}

variable "recipient_emails" {
  description = "Email addresses of the recipients"
  type        = list(string)
  default     = ["sanghwa@amazon.com"]
}

variable "cron" {
  description = "8시 30분에 보내는 예제, cron(Minutes Hours Day-of-month Month Day-of-week Year)"
  type        = string
  default     = "cron(30 8 * * ? *)"
}
