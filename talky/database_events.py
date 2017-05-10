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


@listens_for(Talk, 'after_insert')
def new_talk_assigned(mapper, connection, target):
    """Send notifications if this is the first submission"""
    messages.send_talk_assgined(target)


@listens_for(db.session, 'before_flush')
def talk_reassigned(session, flush_context, instances):
    """Send notifications and change upload_key if the speaker is changed"""
    changed_objects = session.new.union(session.dirty)
    for talk in changed_objects:
        if not isinstance(talk, Talk):
            continue
        attribute_state = inspect(talk).attrs.get('speaker')
        # Check if the speaker has been updated
        history = attribute_state.history
        if not history.has_changes():
            continue
        # Update the upload key
        talk.upload_key = secrets.token_urlsafe()
        # Send a new email to the speaker
        messages.send_talk_assgined(talk)


@listens_for(Submission, 'after_insert')
def new_talk_received(mapper, connection, target):
    """Send notifications if this is the first submission"""
    if target.version == 1:
        messages.send_new_talk_available(target)


@listens_for(Comment, 'after_insert')
def new_comment(mapper, connection, target):
    """Send notifications if this is the first submission"""
    messages.send_new_comment(target)
