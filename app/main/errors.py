from flask import render_template, jsonify, request
from . import main_bp

# 使用HTTP内容协商处理错误 403, 404, 500
@main_bp.app_errorhandler(403)
def http_forbidden(e):
    if request.accept_mimetypes.accept_json and\
        not request.accept_mimetypes.accept_html:
        response = jsonify({'error':'forbidden'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403

@main_bp.app_errorhandler(404)
def page_not_found(e):
    """
    accept_minetypesAccept：请求首部，决定客户端期望接收的响应格式
    API客户端会通常指定响应格式，若接收格式列表包含JSON而不包含HTML时，
    生成JSON响应
    :param e:
    :return:
    """
    if request.accept_mimetypes.accept_json and\
        not request.accept_mimetypes.accept_html:
        # 字典表生成json形式
        response = jsonify({'error':'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and\
        not request.accept_mimetypes.accept_html:
        response = jsonify({'error':'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500