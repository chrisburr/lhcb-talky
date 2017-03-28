from collections import namedtuple
from datetime import datetime

from flask import render_template, abort, redirect, request

from ..talky import app
from .. import schema

Comment = namedtuple(
    'Comment',
    ['id', 'name', 'email', 'comment', 'time', 'submission_version', 'parent_comment_id']
)


def recurse_comments(comments):
    _comments = []
    for c in comments:
        if c.parent_comment_id:
            for i, _c in enumerate(_comments):
                if _c[0] == c.parent_comment_id:
                    _comments[i][-1].append(list(c[:-1]) + [[]])
        else:
            _comments.append(list(c[:-1]) + [[]])
    return _comments


@app.route('/view/<talk_id>/<view_key>/')
def view_talk(talk_id=None, view_key=None):
    talk = schema.Talk.query.get(talk_id)
    if not talk or talk.view_key != view_key:
        abort(404)

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
    )


@app.route('/view/<talk_id>/<view_key>/comment/', methods=['POST'])
def submit_comment(talk_id=None, view_key=None):
    talk = schema.Talk.query.get(talk_id)
    if not talk or talk.view_key != view_key:
        abort(404)

    if not all([request.form['name'].strip(), request.form['email'].strip(), request.form['comment'].strip()]):
        abort(400)

    parent_comment_id = int(request.form['parent_comment_id'])
    print(parent_comment_id, [c.id for c in talk.comments])
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


def create_display():
    pass
