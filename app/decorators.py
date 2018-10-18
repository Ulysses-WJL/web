from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission

# 参数化装饰器func(permission)
# 接收参数
def permission_required(permission):
    # 接收function
    def decorate(func):
        #update_wrapper的装饰器形式
        # 从被装饰的函数func中提取属性attr给修饰器函数decorate
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorate

def admin_required(func):
    return permission_required(Permission.ADMIN)(func)