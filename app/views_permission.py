from flask import make_response, render_template
from flask_login import current_user
from functools import wraps


def admin_check(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.privilege == 'admin':
            return func(*args, **kwargs)
        else:
            return make_response(render_template('forbidden.html'), 403)
    return decorated_view
