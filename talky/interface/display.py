from collections import namedtuple

from flask import render_template, abort

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


@app.route('/view/<talk_id>/<view_key>')
def period_info(talk_id=None, view_key=None):
    # TODO Sanitise talk_id
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


def create_display():
    pass
