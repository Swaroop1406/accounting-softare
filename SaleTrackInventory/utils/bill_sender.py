import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from whatsapp import WhatsApp

class BillSender:
    def __init__(self, smtp_host, smtp_port, smtp_user, smtp_pass, whatsapp_token):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.whatsapp = WhatsApp(token=whatsapp_token)

    def send_email(self, to_email, subject, body, pdf_content):
        """Send bill via email"""
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename='bill.pdf')
        msg.attach(pdf_attachment)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)

    def send_whatsapp(self, phone_number, message, pdf_content):
        """Send bill via WhatsApp"""
        try:
            # Save PDF temporarily
            temp_path = 'temp_bill.pdf'
            with open(temp_path, 'wb') as f:
                f.write(pdf_content)

            # Send message and document via WhatsApp
            self.whatsapp.send_message(phone_number, message)
            self.whatsapp.send_document(phone_number, temp_path)

            # Clean up temporary file
            os.remove(temp_path)
            return True
        except Exception as e:
            print(f"Error sending WhatsApp message: {str(e)}")
            return False
