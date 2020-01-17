from flask import session as flask_session
from flask import flash, url_for, redirect
from flask_login import login_user, current_user, login_fresh

from . import auth_bp
from .oauth import OAuthSignIn
from ..models import User
from ..utils import is_safe_url


@auth_bp.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous and login_fresh():
        return redirect(url_for('main.index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@auth_bp.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous and login_fresh():
        return redirect(url_for('main.index'))

    try:
        dest_page = flask_session['next_url']
        del flask_session['next_url']
        if not is_safe_url(dest_page):
            raise
    except Exception:
        dest_page = url_for('main.index')

    oauth = OAuthSignIn.get_provider(provider)
    access_token, user_info = oauth.callback()

    if access_token is None:
        flash('Authentication failed. Please contact an admin if '
              'this problem is persistent')
        return redirect(url_for('users.login'))

    if provider == 'github':
        username = "gh_" + user_info['login']
        avatar_url = user_info['avatar_url']
    elif provider == 'gitlab':
        username = "gl_" + user_info['username']
        avatar_url = None

    user = User.query.filter_by(_username=username).first()

    if not user:
        flash("No account found. Please submit a request for an account.")
        return redirect(url_for('users.new_account'))

    user.update_avatar(avatar_url)
    login_user(user, remember=True)
    # Token is needed for access to github issues
    flask_session['active_token'] = access_token

    return redirect(dest_page)
