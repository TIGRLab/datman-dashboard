from threading import Thread

from flask_mail import Message

from dashboard import app, mail, SENDER, ADMINS

def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper

@async
def send_async_email(app, email):
    with app.app_context():
        mail.send(email)

def send_email(subject, body, html_body=None, recipient=None):
    if not recipient:
        recipient = ADMINS
    email = Message(subject, sender=SENDER, recipients=recipient)
    email.body = body
    if html_body:
        email.html = html_body
    send_async_email(app, email)

def incidental_finding_email(user, timepoint, comment):
    subject = 'IMPORTANT: Incidental Finding flagged'
    body = '{} has reported an incidental finding for {}. Description: {}'.format(
            user, timepoint, comment)
    send_email(subject, body)

def account_request_email(first_name, last_name):
    subject = "New account request from {} {}".format(first_name,
            last_name)
    dest_url = url_for('manage_users', _external=True)
    html_body = "{} {} has requested dashboard access. <a href='{}'>" \
            "Click here</a> to review and approve/reject the request".format(
            first_name, last_name, dest_url)
    body = "{} {} has requested a dashboard account. Please log in to "\
            "approve or reject this request".format(first_name, last_name)
    send_email(subject, body, html_body=html_body)

def account_activation_email(user):
    return

def account_rejection_email(user):
    return
