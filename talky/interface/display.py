from collections import namedtuple
from datetime import datetime
from os.path import join, isfile

from flask import render_template, abort, redirect, request, send_file
from flask_security import current_user

from ..talky import app
from .. import schema
from ..default_config import file_path

Comment = namedtuple(
    'Comment',
    ['id', 'name', 'email', 'comment', 'time', 'submission_version', 'parent_comment_id']
)


def recurse_comments(comments):
    # Keep an index to keep the structure flat until the final step
    comment_index = {None: [None, None, None, None, None, None, []]}
    for c in comments:
        parent_comment_id = c.parent_comment_id
        c = list(c[:-1]) + [[]]
        comment_index[parent_comment_id][-1].append(c)
        comment_index[c[0]] = c
    return comment_index[None][-1]


def get_talk(talk_id, view_key):
    talk = schema.Talk.query.get(talk_id)
    if not talk or talk.view_key != view_key:
        abort(404)
    return talk


def user_can_edit(talk):
    return current_user.is_authenticated and (
        current_user.experiment == talk.experiment or
        current_user.has_role('superuser')
    )


@app.route('/view/<talk_id>/<view_key>/')
def view_talk(talk_id=None, view_key=None):
    talk = get_talk(talk_id, view_key)

    submissions = [
        [s.id, s.time.strftime("%Y-%m-%d %H:%M")]
        for s in sorted(talk.submissions, key=lambda s: s.time)
    ]

    comments = recurse_comments([Comment(
        c.id, c.name, c.email, c.comment, c.time.strftime("%Y-%m-%d %H:%M"),
        (submissions.index([c.submission.id, c.submission.time.strftime("%Y-%m-%d %H:%M")])+1 if c.submission else None),
        c.parent_comment_id
    ) for c in sorted(talk.comments, key=lambda c: c.time)])

    return render_template(
        'view_id.html',
        talk_id=talk_id,
        title=talk.title,
        abstract=talk.abstract,
        duration=talk.duration,
        speaker=talk.speaker,
        experiment=talk.experiment.name,
        conference_name=talk.conference.name,
        conference_url=talk.conference.url,
        conference_start_date=talk.conference.start_date.date(),
        submissions=submissions,
        comments=comments,
        modify=user_can_edit(talk)
    )


@app.route('/view/<talk_id>/<view_key>/comment/', methods=['POST'])
def submit_comment(talk_id=None, view_key=None):
    talk = get_talk(talk_id, view_key)

    if not all([request.form['name'].strip(), request.form['email'].strip(), request.form['comment'].strip()]):
        abort(400)

    if request.form['parent_comment_id'] == 'None':
        parent_comment_id = None
    else:
        try:
            parent_comment_id = int(request.form['parent_comment_id'])
        except Exception:
            abort(410)
        else:
            if not any(parent_comment_id == c.id for c in talk.comments):
                abort(410)

    if talk.submissions:
        submission = sorted(talk.submissions, key=lambda s: s.time)[-1]
    else:
        submission = None

    comment = schema.Comment(
        name=request.form['name'].strip(),
        email=request.form['email'].strip(),
        comment=request.form['comment'].strip(),
        time=datetime.now(),
        talk=talk,
        submission=submission,
        parent_comment_id=parent_comment_id
    )
    schema.db.session.add(comment)
    schema.db.session.commit()

    return redirect(f'/view/{talk_id}/{view_key}/')


@app.route('/view/<talk_id>/<view_key>/comment/<comment_id>/delete/', methods=['GET'])
def delete_comment(talk_id=None, view_key=None, comment_id=None):
    talk = get_talk(talk_id, view_key)
    if not user_can_edit(talk):
        abort(404)

    try:
        comment_id = int(comment_id)
    except Exception:
        abort(410)

    comment = schema.Comment.query.get(comment_id)
    if not comment or comment.talk != talk:
        abort(404)

    schema.db.session.delete(comment)
    schema.db.session.commit()

    return redirect(f'/view/{talk_id}/{view_key}/')


@app.route('/view/<talk_id>/<view_key>/submission/v<version>/', methods=['GET'])
def view_submission(talk_id=None, view_key=None, version=None):
    talk = get_talk(talk_id, view_key)

    try:
        version = int(version)
    except Exception:
        abort(410)

    submission = talk.submissions.filter(schema.Submission.version == version).first()
    if not submission:
        abort(404)

    submission_fn = join(file_path, str(talk.id), str(submission.version), submission.filename)

    if isfile(submission_fn):
        return send_file(submission_fn)
    else:
        abort(410)


@app.route('/view/<talk_id>/<view_key>/submission/<submission_id>/delete/', methods=['GET'])
def delete_submission(talk_id=None, view_key=None, submission_id=None):
    talk = get_talk(talk_id, view_key)
    if not user_can_edit(talk):
        abort(404)

    try:
        submission_id = int(submission_id)
    except Exception:
        abort(410)

    submission = schema.Submission.query.get(submission_id)
    if not submission or submission.talk != talk:
        abort(404)

    schema.db.session.delete(submission)
    schema.db.session.commit()

    return redirect(f'/view/{talk_id}/{view_key}/')


def create_display():
    pass
