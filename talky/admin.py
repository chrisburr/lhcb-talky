from flask import render_template
import flask_login

from . import app
from .data import Talk


@app.route('/admin')
@flask_login.login_required
def admin():
    return 'Logged in as: ' + flask_login.current_user.id


@app.route('/manage')
@flask_login.login_required
def manage():
    user = flask_login.current_user
    user_talks = user.experiment.talks.all()
    tagged_talks = user.experiment.tagged
    other_talks = [
        t for t in Talk.query.all()
        if t not in user_talks and t not in tagged_talks
    ]

    return render_template(
        'manage.html',
        user=user.email, experiment=user.experiment.name,
        user_talks=user_talks, tagged_talks=tagged_talks, other_talks=other_talks
    )
