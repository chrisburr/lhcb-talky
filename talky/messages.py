from flask_mail import Message

from .talky import mail


def send_talk_assgined(talk):
    msg = Message(f'You have been assigned to a talk - {talk.title}')
    msg.recipients = ['chrisburr73@gmail.com']
    msg.body = 'Congrats!'
    mail.send(msg)


def send_new_talk_available(submission):
    msg = Message(f'New talk uploaded - {submission.talk.title}')
    msg.recipients = ['chrisburr73@gmail.com']
    msg.body = 'New talk uploaded to talky'
    mail.send(msg)


def send_new_comment(comment):
    msg = Message(f'New comment received on {comment.talk.title}')
    msg.recipients = ['chrisburr73@gmail.com']
    msg.body = 'New comment on talk XXX'
    mail.send(msg)
