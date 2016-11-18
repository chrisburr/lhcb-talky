from flask import abort, render_template
import flask_login

from . import app
from . import data


@app.route('/submit/<string:submit_key>')
def talk_submit(submit_key):
    talk = data.Talk.query.filter_by(submit_key=submit_key).first()
    if talk is None:
        abort(404)
    return 'AAAA' + repr(talk)


@app.route('/view/<string:view_key>')
def talk_view(view_key):
    talk = data.Talk.query.filter_by(view_key=view_key).first()
    user = flask_login.current_user
    if talk is None:
        abort(404)

    return render_template(
        'talk_view.html',
        user=user.email, experiment=user.experiment.name,
        talk=talk
    )
