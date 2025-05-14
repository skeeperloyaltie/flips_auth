import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

class GmailOAuth2EmailBackend(BaseEmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credentials = None
        self._load_credentials()

    def _load_credentials(self):
        token_file = os.path.join(settings.BASE_DIR, "token.json")
        creds = None
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, settings.GOOGLE_OAUTH2_SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "web": {
                            "client_id": settings.GOOGLE_OAUTH2_CLIENT_ID,
                            "client_secret": settings.GOOGLE_OAUTH2_CLIENT_SECRET,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": settings.GOOGLE_OAUTH2_TOKEN_URI,
                        }
                    },
                    settings.GOOGLE_OAUTH2_SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(token_file, "w") as token:
                token.write(creds.to_json())
        self.credentials = creds

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        sent_count = 0
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.ehlo()
            server.esmtp_features["auth"] = "XOAUTH2"
            auth_string = self.credentials.token.encode()
            server.docmd("AUTH", f"XOAUTH2 {auth_string.decode()}")
            
            for email_message in email_messages:
                msg = MIMEMultipart()
                msg["From"] = settings.EMAIL_FROM
                msg["To"] = ", ".join(email_message.to)
                msg["Subject"] = email_message.subject
                msg.attach(MIMEText(email_message.body, "plain"))
                
                try:
                    server.sendmail(settings.EMAIL_FROM, email_message.to, msg.as_string())
                    sent_count += 1
                except Exception as e:
                    if not self.fail_silently:
                        raise e
        return sent_count