import os
import smtplib
from email.message import EmailMessage

from secrets import TT_email_user, TT_email_password

EMAIL_ADDRESS  = TT_email_user
EMAIL_PASSWORD = TT_email_password

msg = EmailMessage()
msg['Subject'] = 'Tea Time'
msg['From'] = EMAIL_ADDRESS
msg['To'] = 'reedgwhite@hotmail.com'

# plain text email
msg.set_content('New tee time booked for you!')

# html email
msg.add_alternative("""\
    <!DOCTYPE html>
    <html>
        <body>
            <h1 style="color:#56b000;"> It's Tea Time!</h1>
            <p> Congrats, you've got a new tee time booked! </p>
        </body>
    </html>
    """, subtype='html')

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    # login to mail server
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    smtp.send_message(msg)
