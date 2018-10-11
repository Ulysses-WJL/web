# SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:62300313@localhost:3306/sql_hello?charset=utf8mb4"
# SQLALCHEMY_TRACK_MODIFICATIONS = True
# SECRET_KEY = 'role user test'
#设置这一项是每次请求结束后都会自动提交数据库中的变动
import os
# from user_setting import *
class Config:
    # 防止CSRF攻击， Flask-WTF为所有表单生成安全令牌，根据秘钥生成
    SECRET_KEY = os.environ.get('SECRET_KKEY') or 'you never guess'
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.qq.com'
    MAIL_PORT = os.environ.get('MAIL_PORT') or 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = '2276777056@qq.com'
    FLASK_ADMIN = os.environ.get("FLASK_ADMIN") or 'jianliangwu1171@gmail.com'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_POSTS_PER_PAGE = 25
    FLASK_FOLLOWERS_PER_PAGE = 10
    FLASK_COMMENT_PER_PAGE = 10
    SQLALCHEMY_RECORD_QUERIES = True
    FLASK_SLOW_DB_QUERY_TIME = 0.5
    SSL_REDIRECT = False
    root = 'root'
    passwd = '62300313'
    @staticmethod
    def init_app(app):
        pass
#   开发环境
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    DBNAME = 'sql_hello'
    DBHOST = os.environ.get('DBHOST') or 'localhost'
    URL = f'mysql+pymysql://{root}:{passwd}@{DBHOST}:3306/{DBNAME}'
    SQLALCHEMY_DATABASE_URI = URL
    
class TestingConfig(Config):
    TESTING = True
    DBNAME = 'sql_test'
    #  测试时关闭CSRF保护，不处理令牌
    WTF_CSRF_ENABLED = False
    DBHOST = os.environ.get('DBHOST') or 'localhost'
    URL =  f'mysql+pymysql://{root}:{passwd}@{DBHOST}:3306/sql_test'
    SQLALCHEMY_DATABASE_URI = URL

class ProductioanConfig(Config):
    DEBUG = False
    TESTING = False
    DBNAME = 'sql_product'
    DBHOST = os.environ.get('DBHOST') or 'localhost'
    URL = f'mysql+pymysql://{root}:{passwd}@{DBHOST}:3306/{DBNAME}'
    SQLALCHEMY_DATABASE_URI = URL
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        # 将错误日志以邮件的方式发送给管理员
        mail_handler = SMTPHandler(
            # isinstance(mailhost, (list, tuple)):
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            #         if isinstance(toaddrs, str):
            #             toaddrs = [toaddrs]
            #         self.toaddrs = toaddrs
            toaddrs=[cls.FLASK_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + "Application Error",
            credentials=credentials,
            secure=secure)
        #  Set the logging level of this handler.  level must be an int or a str.
        mail_handler.setLevel(logging.ERROR)
        # Add the specified handler to this logger.
        app.logger.addHandler(mail_handler)
    
# heroku 类的配置
class HerokuConfig(ProductioanConfig):
    """Heroku将应用写入stdout和stderr的输出视为日志"""
    # 使用psycopg2连接Postgres数据库
    DBNAME = 'sql_product'
    DBHOST = os.environ.get('DBHOST') or 'localhost'
    URL = f'psycopg2://{root}:{passwd}@{DBHOST}:3306/{DBNAME}'
    SQLALCHEMY_DATABASE_URI = URL
    SSL_REDIRECT = True if os.environ.get('DYNO') else False
    @classmethod
    def init_app(cls, app):
        ProductioanConfig.init_app(app)
        
        # 检查client->reverse proxy的请求的首部，是否加密request.is_secure
        # 处理reverse proxy -> Web应用 设定的首部
        # 使用ProxyFix中间件
        from werkzeug.contrib.fixers import ProxyFix
        # add HTTP proxy support to an
        #  application that was not designed with HTTP proxies in mind
        app.wsgi_app = ProxyFix(app.wsgi_app)
        
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        


config = {
    'development': DevelopmentConfig,
    'default': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductioanConfig,
    'heroku':HerokuConfig
}
