from flask import render_template
from . import main_bp

# 错误处理函数
@main_bp.app_errorhandler(403)
def http_forbidden(e):
    return render_template('403.html'), 403

@main_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main_bp.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500