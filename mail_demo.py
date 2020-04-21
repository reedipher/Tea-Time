import os
import smtplib
from secrets import TT_email_user, TT_email_password

EMAIL_ADDRESS  = TT_email_user
EMAIL_PASSWORD = TT_email_password

with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
    smtp.ehlo()

    # encrypt traffic
    smtp.starttls()

    # reidentify as an encrypted connection
    smtp.ehlo()

    print(EMAIL_ADDRESS, EMAIL_PASSWORD)

    # login to mail server
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    subject = 'Tea Time'
    body    = 'New tee time booked for you'

    msg = f'Subject: {subject}\n\n{body}'

    smtp.sendmail(EMAIL_ADDRESS, 'reedgwhite@hotmail.com', msg)