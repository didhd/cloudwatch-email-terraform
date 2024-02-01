# 클라우드워치 대시보드 스냅샷 이메일러

이 프로젝트는 AWS Lambda를 사용하여 Amazon CloudWatch 대시보드의 스냅샷을 캡처하고 AWS Simple Email Service (SES)를 통해 이를 자동으로 이메일로 보내는 솔루션을 구현합니다.

## 구성 요소

- `lambda_function.py`: 대시보드의 스냅샷을 캡처하고 이메일로 보내는 AWS Lambda 함수.
- `나머지`: AWS 리소스를 프로비저닝하는 Terraform 구성 파일들이 포함된 디렉토리.

## 시작하기

이 프로젝트를 사용하기 위해서는 AWS 계정이 필요하며, AWS CLI가 올바르게 구성되어 있어야 합니다.

1. Terraform을 설치합니다.
2. `variables.tf` 파일을 수정합니다.
3. 터미널에 `terraform init && terraform apply` 입력: 디렉토리 내의 Terraform 구성 파일들을 사용하여 AWS 리소스를 배포합니다.
4. **SES 이메일 주소 인증**:
   AWS SES에서 이메일을 보내기 위해 발신자 이메일 주소를 인증해야 합니다. AWS Management Console에서 SES 대시보드로 이동하여 발신자 이메일 주소를 인증합니다. (https://ap-northeast-2.console.aws.amazon.com/ses/home?region=ap-northeast-2#/verified-identities)
5. 매일 8시 30분에 대시보드 알림이 전달됩니다.


## 환경 변수

Lambda 함수는 다음 환경 변수를 사용합니다:

- `DASHBOARD_NAME`: 캡처할 CloudWatch 대시보드의 이름.
- `SENDER_EMAIL`: 이메일 발신자 주소 (AWS SES에서 인증된 주소여야 합니다).
- `RECIPIENT_EMAILS`: 이메일 수신자 주소.