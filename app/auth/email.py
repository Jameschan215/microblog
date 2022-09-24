from flask import render_template, current_app
from app.email import send_mail


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    subject = '[Microblog] Reset Your Password'
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    recipients = [user.email]
    text_body = render_template('email/reset_password.txt', user=user, token=token)
    html_body = render_template('email/reset_password.html', user=user, token=token)

    send_mail(subject=subject, sender=sender, recipients=recipients, text_body=text_body, html_body=html_body)
    