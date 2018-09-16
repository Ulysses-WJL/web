from app import db

class User(db.Model):
    #  该表在数据库中的名字
    __tablename__ = 'users'
    # 结构 primary_key 主键
    # unique 不允许重复
    # index 为列创建索引
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(30), unique=True, index=True)
    pass_wd = db.Column(db.String(30), default='123456')
    # role_id 外键， 此列值时role表中的role_id值
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'))

    def __repr__(self):
        return f'<User {self.user_name}>'


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

