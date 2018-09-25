from flask import render_template, Flask, url_for, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_mail import Mail
from config import config
from flask_login import LoginManager
from flask_pagedown import PageDown
# import pymysql


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
# This object is used to hold the settings used for logging in.
login_manager = LoginManager()
#: The name of the view to redirect to when the user needs to log in.
#: (This can be an absolute URL as well, if your authentication
#: machinery is external to your application.)
#: 设置登录界面的端点
login_manager.login_view = 'auth_bp.login'
# 使用PageDownField之前要初始化扩展
pagedown = PageDown()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    # 在应用中注册该蓝图
    from .main import main_bp
    from .auth import auth_bp
    from .user import user_bp
    from .role import role_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    
    return app
# app = Flask(__name__)
# app.config.from_object('config')
# db = SQLAlchemy(app)
# from . import models,views