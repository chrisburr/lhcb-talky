from flask import render_template, abort

from ..talky import app
from .. import schema


@app.route('/view/<talk_id>/')
def period_info(talk_id=None):
    # TODO Sanitise talk_id
    talk = schema.Talk.query.get(talk_id)
    if not talk:
        abort(404)

    submissions = [
        [submission.id, submission.time.strftime("%Y-%m-%d %H:%M")]
        for submission in sorted(talk.submissions, key=lambda s: s.time)
    ]

    print('*'*10, talk)
    print('*'*10, submissions)
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
        comments=[]
    )


def create_display():
    pass
