from flask_mail import Message

from . import schema
from .talky import app, mail


def _validate_emails(emails):
    """While debugging ensure all emails are sent to me"""
    for email in emails:
        assert email.startswith('chrisburr73'), email
        assert email[len('chrisburr73')] in ['@', '+'], email
        assert email.endswith('@gmail.com'), email
    return emails


def send_talk_assgined(talk):
    msg = Message(f'You have been assigned to a talk - {talk.title}')
    msg.html = (
        f'Dear speaker,\n'
        f'\n'
        f'You have been assigned to the talk entitled "<a href='
        f'"{app.config["TALKY_DOMAIN"]}/view/{talk.id}/{talk.view_key}/"'
        f'>{talk.title}</a>" at {talk.conference.name} starting on '
        '{talk.conference_date}.\n'
        f'\n'
        f'Please upload you presentation and any further revisions using the '
        f'form <a href='
        f'"{app.config["TALKY_DOMAIN"]}/upload/{talk.id}/{talk.upload_key}/"'
        f'>available here</a>. '
        f'After uploading your slides all relevant parties will be notified '
        f'and able to make comments.\n'
        f'\n'
        f'Issues with talky can be reported using the <a href='
        f'"https://github.com/chrisburr/lhcb-talky">talky issue tracker</a>.\n'
    )
    msg.reply_to = _validate_emails(['chrisburr73+reply_to@gmail.com'])[0]
    msg.recipients = _validate_emails([talk.speaker])
    mail.send(msg)


def send_new_talk_available(submission):
    talk = submission.talk
    msg = Message(f'New talk uploaded - {submission.talk.title}')
    msg.recipients = ['chrisburr73@gmail.com']
    msg.body = (
        f'You have received this email as you have been flagged as an '
        f'interested party in the talk entitled "<a href='
        f'"{app.config["TALKY_DOMAIN"]}/view/{talk.id}/{talk.view_key}/"'
        f'>{talk.title}</a>" at that will be given at {talk.conference.name} '
        f'starting on {talk.conference_date}.\n'
        f'\n'
        f'Slides are now available to view and you may leave comments on the '
        f'above page. You will not be notified of further revisions however '
        f'you will be in the event someone replies to a comment left by you.\n'
        f'\n'
        f'Issues with talky can be reported using the <a href='
        f'"https://github.com/chrisburr/lhcb-talky">talky issue tracker</a>.\n'
    )
    _validate_emails(msg.recipients)
    msg.reply_to = _validate_emails(['chrisburr73+reply_to@gmail.com'])[0]
    # Send notifications to the members of this and flagged experiments
    recipients = []
    for user in schema.Talk.query.all():
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
    mail.send(msg)


def send_new_comment(comment):
    talk = comment.talk
    msg = Message(f'New comment received on {comment.talk.title}')
    msg.recipients = ['chrisburr73@gmail.com']
    msg.body = (
        f'A new comment has been submitted by '
        f'<a href="mailto:{comment.email}">{comment.name}</a> on "<a href='
        f'"{app.config["TALKY_DOMAIN"]}/view/{talk.id}/{talk.view_key}/"'
        f'>{talk.title}</a>" at that will be given at {talk.conference.name} '
        f'starting on {talk.conference_date}.\n'
        f'\n'
        f'The comment text is:\n'
        f'{comment.comment}\n'
        f'\n'
        f'You may reply using the talk page linked above.\n'
        f'\n'
        f'Issues with talky can be reported using the <a href='
        f'"https://github.com/chrisburr/lhcb-talky">talky issue tracker</a>.\n'
    )
    _validate_emails(msg.recipients)
    msg.reply_to = _validate_emails(['chrisburr73+reply_to@gmail.com'])[0]
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
    mail.send(msg)
