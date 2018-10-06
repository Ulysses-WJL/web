"""Flask-httpauth authentication 身份验证
web应用是使用flask-login 将数据存储在session中，会话会被存储在客户端cookie中
web服务，使用 HTTP身份验证发送凭据，用户凭据包含在每个请求的Authorization首部中
"""
from flask_httpauth import HTTPBasicAuth
from flask import g, jsonify
from ..models import User
from .errors import unauthorized, forbidden
from . import api_bp

auth = HTTPBasicAuth()

# auth.verify_password传递回调函数给HTTPBasicAuth，
# 验证时会调用这个回调函数
# 为了避免直接发送密码等敏感信息，使用基于令牌的身份验证Serializer
@auth.verify_password
def verify_password(email_or_token, password):
    # 请求的信息没有邮箱也没有身份令牌token, 为匿名用户
    if email_or_token == "":
        return False
    # 没有密码， 通过token进行验证
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        # 可选择通过哪种方式验证
        g.token_used = True
        return g.current_user is not None
    # 通过邮箱-密码进行身份验证
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    # 获取user后，保存在Flask上下文变量g（保存每个请求要用到的请求内的全局变量）中
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)

# 身份验证错误处理 成功status_code 200， 错误401
@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')

# api_bp 所有蓝本下的视图函数进行保护
# 非匿名用户且没有进行验证时，403
@api_bp.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('Unconfirmed account')

# 请求生成身份验证令牌
@api_bp.route('/tokens/', methods=['POST'])
def get_token():
    # 必须要使用邮箱-密码进行验证，而不是旧令牌
    if g.current_user.is_anonymous or g.token_used:
        unauthorized('Invalid credentials')
    return jsonify({'token':g.current_user.generate_auth_token(
        expiration=3600), 'expiration':3600})


