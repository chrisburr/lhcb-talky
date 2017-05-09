from collections import namedtuple
from datetime import datetime
import os
from os.path import join, isfile, isdir

from flask import render_template, abort, redirect, request, send_file, url_for
from flask_security import current_user
from werkzeug.utils import secure_filename

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


def get_talk(talk_id, view_key=None, manage_key=None):
    talk = schema.Talk.query.get(talk_id)
    if not (view_key or manage_key):
        raise RuntimeError()
    if not talk:
        abort(404)
    if view_key and talk.view_key != view_key:
        abort(404)
    if manage_key and talk.manage_key != manage_key:
        abort(404)
    return talk


def user_can_edit(talk):
    return current_user.is_authenticated and (
        current_user.experiment == talk.experiment or
        current_user.has_role('superuser')
    )


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['pdf']


@app.route('/manage/<talk_id>/<manage_key>/', methods=['GET', 'POST'])
def manage_talk(talk_id=None, manage_key=None):
    talk = get_talk(talk_id, manage_key=manage_key)

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            raise NotImplementedError('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            raise NotImplementedError('No selected file')
            return redirect(request.url)

        if not (file and allowed_file(file.filename)):
            raise NotImplementedError('Invalid file')
            return redirect(request.url)

        # Prepare the upload folder
        talk.n_submissions += 1
        version = talk.n_submissions
        submission_dir = join(file_path, str(talk.id), str(version))
        if isdir(submission_dir):
            print('WARNING: INTERNAL SERVER ERROR! - Recovering...')
            while isdir(submission_dir):
                talk.n_submissions += 1
                version = talk.n_submissions
                submission_dir = join(file_path, str(talk.id), str(version))
        os.makedirs(submission_dir)

        filename = secure_filename(file.filename)
        file.save(join(submission_dir, filename))

        submission = schema.Submission(
            talk=talk, time=datetime.now(), version=version,
            filename=filename
        )
        schema.db.session.add(submission)
        schema.db.session.commit()
        # flash(f'Uploaded v{XX} sucessfully')
        return redirect(f'/view/{talk.id}/{talk.view_key}/')

    return render_template(
        'manage_id.html',
        talk_id=talk_id,
        title=talk.title,
        modify=user_can_edit(talk)
    )


@app.route('/view/<talk_id>/<view_key>/')
def view_talk(talk_id=None, view_key=None):
    talk = get_talk(talk_id, view_key=view_key)

    submissions = [
        [s.id, s.version, s.time.strftime("%Y-%m-%d %H:%M")]
        for s in sorted(talk.submissions, key=lambda s: s.time)
    ]

    comments = recurse_comments([Comment(
        c.id, c.name, c.email, c.comment, c.time.strftime("%Y-%m-%d %H:%M"),
        c.submission.version if c.submission else None, c.parent_comment_id
    ) for c in sorted(talk.comments, key=lambda c: c.time)])

    return render_template(
        'view_id.html',
        talk_id=talk_id,
        manage_key=talk.manage_key,
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
        modify=user_can_edit(talk),
        n_submissions=talk.n_submissions
    )


@app.route('/view/<talk_id>/<view_key>/comment/', methods=['POST'])
def submit_comment(talk_id=None, view_key=None):
    talk = get_talk(talk_id, view_key=view_key)

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
    talk = get_talk(talk_id, view_key=view_key)
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
    talk = get_talk(talk_id, view_key=view_key)

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
    talk = get_talk(talk_id, view_key=view_key)
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
