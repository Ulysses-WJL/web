from . import api_bp
from app.exceptions import ValidationError
from flask import jsonify
"""
（404,500flask自己生成 返回html响应）错误在main.error处理，由http内容协商机制处理
其余错误由web服务生成
"""
# 403 禁止
def forbidden(message):
    response = jsonify({'error':'forbidden', 'message':message})
    response.status_code = 403
    return response

# 400 bad requset
def bad_request(message):
    response = jsonify({'error':'bad request', 'message':message})
    response.status_code = 400
    return response

# 401 unauthorized
def unauthorized(message):
    response = jsonify({'error':'unauthorized', 'message':message})
    response.status_code = 401
    return response

# 405 not allowed
def not_allowed(message):
    response = jsonify({'error':'method not allowed', 'message':message})
    response.status_code = 405
    return response
# 其余错误， 请求出错
# 只要抛出了指定类的异常，就会调用被装饰的函数
@api_bp.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])

class ValidationError(ValueError):
    pass
