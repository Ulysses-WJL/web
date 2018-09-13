from app import app
from .role import role_bp
from .user import user_bp
# 在应用中注册该蓝图app.register_blueprint(blueprint)，
app.register_blueprint(role_bp)
app.register_blueprint(user_bp)