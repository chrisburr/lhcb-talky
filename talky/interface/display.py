from collections import namedtuple
from datetime import datetime
import os
from os.path import join, isfile, isdir
import logging as log

from flask import render_template, abort, redirect, request, send_file, flash
from flask_security import current_user
from werkzeug.utils import secure_filename

from ..talky import app
from .. import schema

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


def get_talk(talk_id, view_key=None, upload_key=None):
    talk = schema.Talk.query.get(talk_id)
    if not (view_key or upload_key):
        raise RuntimeError()
    if not talk:
        log.warning(f'Failed to find Talk with id == {talk_id}')
        abort(404)
    if view_key and talk.view_key != view_key:
        log.warning(f'Incorrect view_key ({view_key}) given for Talk {talk_id}')
        abort(404)
    if upload_key and talk.upload_key != upload_key:
        log.warning(f'Incorrect upload_key ({upload_key}) given for Talk {talk_id}')
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


@app.route('/upload/<talk_id>/<upload_key>/', methods=['GET', 'POST'])
def upload_submission(talk_id=None, upload_key=None):
    talk = get_talk(talk_id, upload_key=upload_key)

    if request.method == 'POST':
        log.info(f'{current_user} is uploading a talk for {talk_id}')
        # Check if the post request has the file part
        if 'file' not in request.files:
            log.error(f'Request did not contain files')
            flash('Invalid request', 'error')
            abort(400)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            log.error(f'No file given for submission')
            flash('No file specified', 'error')
            return redirect(request.url)

        if not (file and allowed_file(file.filename)):
            log.error(f'Invalid file submission attempted, aborting')
            flash('Invalid filename or extension (only pdf is permitted)', 'error')
            return redirect(request.url)

        # Prepare the upload folder
        talk.n_submissions += 1
        version = talk.n_submissions
        submission_dir = join(app.config['FILE_PATH'], str(talk.id), str(version))
        if isdir(submission_dir):
            log.warning('Submission directory already exists, recovering')
            while isdir(submission_dir):
                talk.n_submissions += 1
                version = talk.n_submissions
                submission_dir = join(app.config['FILE_PATH'], str(talk.id), str(version))
        os.makedirs(submission_dir)

        filename = secure_filename(file.filename)
        log.info(f'Uploading submission v{version} for talk {talk_id} with '
                 f'filename {filename} to {submission_dir}')
        file.save(join(submission_dir, filename))

        submission = schema.Submission(
            talk=talk, time=datetime.now(), version=version,
            filename=filename
        )
        schema.db.session.add(submission)
        schema.db.session.commit()
        log.info(f'Submission {submission.id} successfully uploaded')
        return redirect(f'/view/{talk.id}/{talk.view_key}/')
    else:
        return render_template(
            'upload_submission.html',
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
        'view_talk.html',
        talk_id=talk_id,
        upload_key=talk.upload_key,
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

    if '@' not in request.form['email']:
        abort(400)

    if request.form['parent_comment_id'] == 'None':
        parent_comment_id = None
    else:
        try:
            parent_comment_id = int(request.form['parent_comment_id'])
        except Exception:
            abort(400)
        else:
            if not any(parent_comment_id == c.id for c in talk.comments):
                abort(400)

    if talk.submissions.all():
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
        log.warning(f'Error parsing version as integer')
        abort(410)

    submission = talk.submissions.filter(schema.Submission.version == version).first()
    if not submission:
        log.warning(f'Failed to find submission submission v{version} in talk {talk_id}')
        abort(404)

    submission_fn = join(app.config['FILE_PATH'], str(talk.id), str(submission.version), submission.filename)

    if isfile(submission_fn):
        log.info(f'Sending {submission_fn} for submission v{version} in talk {talk_id}')
        return send_file(submission_fn)
    else:
        log.warning(f'Failed to find file submission v{version} for talk {talk_id}')
        abort(410)


@app.route('/view/<talk_id>/<view_key>/submission/<submission_id>/delete/', methods=['GET'])
def delete_submission(talk_id=None, view_key=None, submission_id=None):
    talk = get_talk(talk_id, view_key=view_key)
    if not user_can_edit(talk):
        log.warning(f'Blocked attempt to delete submission {submission_id} for talk {talk_id}')
        abort(404)

    try:
        submission_id = int(submission_id)
    except Exception:
        log.warning(f'Error parsing submission_id as integer')
        abort(410)

    submission = schema.Submission.query.get(submission_id)
    if not submission or submission.talk != talk:
        log.warning(f'Invalid submission id ({submission_id}) passed for talk {talk_id}')
        abort(404)

    log.info(f'Removing submission {submission_id} for talk {talk_id}')
    schema.db.session.delete(submission)
    schema.db.session.commit()

    return redirect(f'/view/{talk_id}/{view_key}/')


@app.route('/delete/<talk_id>/<view_key>/', methods=['GET'])
def delete_talk(talk_id=None, view_key=None):
    talk = get_talk(talk_id, view_key=view_key)
    if not user_can_edit(talk):
        log.warning(f'Blocked attempt to delete talk {talk_id}')
        abort(404)

    log.info(f'Removing talk {talk_id}')
    schema.db.session.delete(talk)
    schema.db.session.commit()

    return redirect(f'/')
