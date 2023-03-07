from functools import wraps

from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def login_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims['logged_in'] != 'true':
                return jsonify(msg='Please log in!'), 403
            else:
                return fn(*args, **kwargs)
        return decorator
    return wrapper


def reset_permitted():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            return (claims)
            if claims['reset_permitted'] != 'true':
                return jsonify(msg='You do not have permission to access this resource'), 403
            else:
                return fn(*args, **kwargs)
        return decorator
    return wrapper
