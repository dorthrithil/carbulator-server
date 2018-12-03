import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app, render_template

from src.models.user import UserModel


def send_forgot_password_email(user: UserModel):
    """
    Sends a reset password mail to the user.
    :param user: User to send the reset mail to.
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Carbulator Passwort zurücksetzen"
    msg['From'] = current_app.config['SYSTEM_EMAIL']
    msg['To'] = user.email
    action_link = '{}/reset-password/{}'.format(current_app.config['FRONTEND_HOST'], user.reset_password_hash)
    template = render_template('reset-password-mail.html', name=user.username, action_link=action_link)
    msg.attach(MIMEText(template, 'html'))
    s = smtplib.SMTP_SSL(current_app.config['SMTP_HOST'], current_app.config['SMTP_PORT'])
    s.login(current_app.config['SMTP_USER'], current_app.config['SMTP_PASSWORD'])
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()
