import flask
from flask import render_template, redirect
import flask_login

from . import app
from . import data

# Set up the login manager
login_manager = flask_login.LoginManager()
login_manager.init_app(app)


# class User(flask_login.UserMixin):
#     pass


@login_manager.user_loader
def user_loader(email):
    db_user = data.User.query.get(email)
    if db_user is None:
        return

    user = db_user
    # user = User()
    # user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    if email is None:
        return
    db_user = data.User.query.get(email)
    if db_user is None:
        return

    user = db_user
    # user = User()
    # user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['pw'] == db_user.password
    return user


@app.route('/')
def index():
    return redirect("/login", code=302)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return render_template('login.html')

    email = flask.request.form['email']
    db_user = data.User.query.get(email)
    if db_user and flask.request.form['pw'] == db_user.password:
        print(flask.request.form['pw'], db_user.password)
        user = db_user
        # user.id = email
        flask_login.login_user(user, remember=False)
        return flask.redirect(flask.url_for('manage'))

    return render_template('login.html', error='Bad login details')


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect("/login", code=302)


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect("/login", code=302)
