import boto3
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# 환경 변수에서 이메일 정보를 가져옵니다.
SENDER = os.environ["SENDER_EMAIL"]
RECIPIENTS = os.environ["RECIPIENT_EMAILS"].split(",")

# AWS 클라이언트를 초기화합니다.
cloudwatch = boto3.client("cloudwatch")
ses = boto3.client("ses")


def lambda_handler(event, context):
    # 대시보드 이름을 가져옵니다.
    dashboard_name = os.environ["DASHBOARD_NAME"]

    # 대시보드의 위젯들을 리스트업합니다.
    dashboard_response = cloudwatch.get_dashboard(DashboardName=dashboard_name)
    dashboard_body = json.loads(dashboard_response["DashboardBody"])

    # 이메일 메시지를 생성합니다.
    msg = MIMEMultipart("mixed")
    msg["Subject"] = "Your Daily CloudWatch Dashboard Snapshot"
    msg["From"] = SENDER
    msg["To"] = ", ".join(RECIPIENTS)

    # HTML과 텍스트 본문을 위한 'alternative' 파트를 생성합니다.
    alt_part = MIMEMultipart("alternative")

    # 텍스트 본문 생성 및 첨부
    text_part = MIMEText("This is the alternative plain text message.", "plain")
    alt_part.attach(text_part)

    # 대시보드 위젯 정보를 파싱합니다.
    widgets = dashboard_body["widgets"]
    html_rows = {}

    for widget in widgets:
        if widget["type"] == "metric":
            # 위젯의 프로퍼티에서 필요한 정보를 추출합니다.
            widget_props = widget.get("properties")
            metric_widget = {
                "metrics": widget_props.get("metrics", []),
                "region": str(widget_props.get("region", "")),
            }
            # 위젯 속성 추가...

            # CloudWatch get_metric_widget_image API 호출
            response = cloudwatch.get_metric_widget_image(
                MetricWidget=json.dumps(metric_widget)
            )
            img_data = response["MetricWidgetImage"]
            if img_data:  # 이미지 데이터가 있는지 확인
                img = MIMEImage(img_data)
                content_id = f"widget-{widget_props.get('title', 'default').replace(' ', '_').replace('(', '').replace(')', '')}"  # 특수 문자 제거
                img.add_header("Content-ID", f"<{content_id}>")
                msg.attach(img)  # 이미지 첨부

                # 위젯의 레이아웃 정보를 기반으로 HTML 테이블 row를 구성합니다.
                row_index = widget.get("y", 0)  # y 좌표는 row 인덱스로 사용됩니다.
                if row_index not in html_rows:
                    html_rows[row_index] = []

                # 위젯의 HTML을 준비합니다. 여기서는 간단히 width를 사용하여 셀 크기를 조정합니다.
                widget_html = f"""
                <td class="widget-cell" style="width: {widget['width']}%;"><img src="cid:{content_id}" alt="{content_id}"></td>
                """
                html_rows[row_index].append(widget_html)

        if widget["type"] == "text":
            widget_props = widget.get("properties")
            widget_html = f"""
                <td>{widget_props.get("markdown")}</td>
                """
            row_index = widget.get("y", 0)  # y 좌표는 row 인덱스로 사용됩니다.
            if row_index not in html_rows:
                html_rows[row_index] = []
            html_rows[row_index].append(widget_html)

    # HTML 본문을 준비합니다.
    html_body_start = """
    <html>
        <head>
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    color: #333;
                }
                .dashboard-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .widget-cell {
                    vertical-align: top;
                    padding: 10px;
                    border: 1px solid #ddd;
                }
                img {
                    width: 100%;
                    height: auto;
                    border: 0;
                }
                h1 {
                    color: #007bff;
                }
                p {
                    font-size: 16px;
                }
            </style>
        </head>
        <body>
            <h1>Your Daily CloudWatch Dashboard Snapshot</h1>
            <p>Find your dashboard snapshots below:</p>
            <table class="dashboard-table">
    """

    html_body_end = """
            </table>
        </body>
    </html>
    """

    # 각 row의 HTML을 조합하여 전체 테이블 HTML을 완성합니다.
    html_body_content = ""
    for row_index in sorted(html_rows.keys()):
        row_html = "<tr>" + "".join(html_rows[row_index]) + "</tr>"
        html_body_content += row_html

    # 최종 HTML 본문을 완성합니다.
    html_body = html_body_start + html_body_content + html_body_end

    # HTML 본문 생성 및 첨부
    html_part = MIMEText(html_body, "html")
    alt_part.attach(html_part)

    # 'alternative' 파트를 'mixed' 메시지에 첨부합니다.
    msg.attach(alt_part)

    # SES를 통해 이메일을 보냅니다.
    try:
        ses.send_raw_email(
            Source=SENDER,
            Destinations=RECIPIENTS,
            RawMessage={"Data": msg.as_string()},
        )
    except Exception as e:
        print(e)
        raise e

    return {"statusCode": 200, "body": "Email sent successfully!"}
