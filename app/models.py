from app import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from . import login_manager


class User(UserMixin, db.Model):
    #  该表在数据库中的名字
    __tablename__ = 'users'
    # 结构 primary_key 主键
    # unique 不允许重复
    # index 为列创建索引
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    user_name = db.Column(db.String(30), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    # role_id 外键， 此列值时role表中的role_id值
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'))
    # UserMixin 需要，get_id()
    id = user_id
    
    def __repr__(self):
        return f'<User {self.user_name}>'

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        # 计算密码散列值
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Role(db.Model):
    __tablename__ = 'role'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(20), unique=True, index=True)
    role_level = db.Column(db.Integer)
    # 关系选项 ‘一’的那端使用relationship,
    # backref在User模型中添加role属性，定义反向关系,可以通过这个属性获取对应Role模型对象
    # 不在通过role_id外键
    # User.query.filter_by(role=first_role)
    users = db.relationship('User', backref='role', lazy='dynamic')
    # role_1.users 返回使用role_1的user对象列表
    def __repr__(self):
        return f'<Role {self.role_name}>'


"""将注册函数load_user传入给flask_login（load_user->self.user_callback）
reload_user时检测根据传入user_id确定的user是否存在（installed），不存在则抛出异常
存在，则为ctx.user
"""
@login_manager.user_loader
def load_user(user_id):
    # 先将传入的字符串转为整数
    return User.query.get(int(user_id))
