import logging
from threading import Thread

from flask_mail import Message
from jinja2 import Environment, PackageLoader, select_autoescape
from premailer import transform
import cssutils

from . import schema
from .talky import app, mail

# Suppress error messages from premailer
cssutils.log.setLevel(logging.CRITICAL)

env = Environment(
    loader=PackageLoader('talky', 'templates/email'),
    autoescape=select_autoescape(['html', 'xml'])
)


def send_async_email(app, msg):
    with app.app_context():
        # TODO Notify me if this goes wrong
        mail.send(msg)


def _validate_emails(emails):
    """While debugging ensure all emails are sent to me"""
    for email in emails:
        assert email.startswith('chrisburr73'), email
        assert email[len('chrisburr73')] in ['@', '+'], email
        assert email.endswith('@gmail.com'), email
    return emails


def send_talk_assgined(talk):
    subject = f'You have been assigned to a talk - {talk.title}'
    msg = Message(subject)
    msg.html = transform(env.get_template('talk_assigned.html').render(
        subject=subject,
        talk=talk,
        domain=app.config['TALKY_DOMAIN']
    ))
    msg.recipients = _validate_emails([talk.speaker])

    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()


def send_new_talk_available(submission):
    talk = submission.talk
    subject = f'New talk uploaded - {submission.talk.title}'

    msg = Message(subject)
    msg.html = transform(env.get_template('new_talk_available.html').render(
        subject=subject,
        talk=talk,
        domain=app.config['TALKY_DOMAIN']
    ))

    # Send notifications to the members of this and flagged experiments
    recipients = []
    for user in schema.User.query.all():
        if user.experiment == talk.experiment:
            recipients.append(user.email)
        elif user.experiment in talk.interesting_to:
            recipients.append(user.email)
    # Send notifications to members of flagged categories
    for category in talk.categories:
        recipients.extend([c.email for c in category.contacts])
    # Remove duplicates
    recipients = list(set(recipients))
    # Sent the email
    msg.bcc = _validate_emails(recipients)

    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()


def send_new_comment(comment):
    talk = comment.talk
    subject = f'New comment received on {comment.talk.title}'

    msg = Message(subject)
    msg.html = transform(env.get_template('new_comment.html').render(
        subject=subject,
        talk=talk,
        comment=comment,
        domain=app.config['TALKY_DOMAIN']
    ))

    # Always sent notification if replies to the speaker
    recipients = [talk.speaker]
    # TODO Send notification of the replies to any parent commentators
    # Remove duplicates
    recipients = list(set(recipients))
    # Remove the commenter if they are in the recipients
    if comment.email in recipients:
        recipients.pop(recipients.index(comment.email))
    # Sent the email
    msg.bcc = _validate_emails(recipients)

    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
