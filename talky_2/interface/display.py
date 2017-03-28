from flask import render_template

from ..talky import app


@app.route('/view/<talk_id>/')
def period_info(talk_id=None):
    return render_template(
        'view_id.html',
        talk_id=talk_id
    )


def create_display():
    pass
