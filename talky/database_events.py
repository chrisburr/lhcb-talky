import os
from os.path import join
import secrets

from sqlalchemy.event import listens_for
from sqlalchemy import inspect

from .talky import app
from .schema import db, Submission, Talk, Comment
from . import messages


@listens_for(Submission, 'after_delete')
def delete_file(mapper, connection, target):
    """Delete files if a submission has been deleted"""
    if target.filename and app.config['CLEANUP_FILES']:
        try:
            os.remove(join(app.config['FILE_PATH'], str(target.talk.id),
                      str(target.version), target.filename))
        except OSError:
            # We don't care if wasn't deleted because it does not exist
            pass


@listens_for(db.session, 'before_flush')
def monitor_db_before_flush(session, flush_context, instances):
    """Monitor for changes in the database"""
    changed_objects = session.new.union(session.dirty)
    for obj in changed_objects:
        if isinstance(obj, Talk):
            update_upload_key(obj)


def update_upload_key(talk):
    """If the speaker changes generate a new modified key"""
    attribute_state = inspect(talk).attrs.get('speaker')
    # Check if the speaker has been updated
    history = attribute_state.history
    if history.has_changes():
        # Update the upload key
        talk.upload_key = secrets.token_urlsafe()


@listens_for(db.session, 'after_flush')
def monitor_db_after_flush(session, flush_context):
    """Monitor for changes in the database"""
    changed_objects = session.new.union(session.dirty)
    for obj in changed_objects:
        if isinstance(obj, Talk):
            talk_changed(obj)
        if isinstance(obj, Submission):
            submission_received(obj)
        if isinstance(obj, Comment):
            new_comment(obj)


def talk_changed(talk):
    """If the speaker changes notify them"""
    attribute_state = inspect(talk).attrs.get('speaker')
    # Check if the speaker has been updated
    history = attribute_state.history
    if history.has_changes():
        # Send a new email to the speaker
        messages.send_talk_assgined(talk)


def submission_received(submission):
    """Send notifications if this is the first submission"""
    attribute_state = inspect(submission).attrs.get('version')
    # Check if the speaker has been updated
    history = attribute_state.history
    # TODO Check for insert rather than assuming the version is immutable
    if history.has_changes() and submission.version == 1:
        messages.send_new_talk_available(submission)


def new_comment(comment):
    """Send notifications of new comments"""
    attribute_state = inspect(comment).attrs.get('comment')
    # Check if the speaker has been updated
    history = attribute_state.history
    # TODO Check for insert rather than assuming the comment is immutable
    if history.has_changes():
        messages.send_new_comment(comment)
