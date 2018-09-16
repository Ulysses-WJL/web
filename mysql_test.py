from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)


# 配置flask-wtf 秘钥
app.config['SECRET_KEY'] = 'secret key'
# 数据库所在url,配置到flask的设置中
DBNAME = 'sqltest'
URL = 'mysql+pymysql://root:62300313@localhost:3306/sqltest'
app.config['SQLALCHEMY_DATABASE_URI'] = URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app=app)
# db.init_app(app)

# 数据库中的2个表 映射为 python类
class User(db.Model):
    #  该表在数据库中的名字
    __tablename__ = 'users'
    # 结构 primary_key 主键
    # unique 不允许重复
    # index 为列创建索引
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String, unique=True, index=True)
    pass_wd = db.Column(db.String)
    # role_id 外键
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'))

    def __repr__(self):
        return f'<User {self.user_name}>'


class Role(db.Model):
    __tablename__ = 'role'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String, unique=True, index=True)
    # 关系选项 ‘一’的那端使用relationship
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return f'<Role {self.role_name}>'
if __name__ == '__main__':
    app.run()
