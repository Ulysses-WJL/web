from functools import wraps
from flask import g
from ..models import Permission
from .errors import forbidden

# 参数化装饰器func(permission)
# 接收参数
def permission_required(permission):
    # 接收function
    def decorator(func):
        #update_wrapper的装饰器形式
        # 从被装饰的函数func中提取属性attr给修饰器函数decorate
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden("Insufficient permissions")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(func):
    return permission_required(Permission.ADMIN)(func)