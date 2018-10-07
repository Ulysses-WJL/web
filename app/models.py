import hashlib
from app import db
from flask import current_app,request,url_for
from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from datetime import datetime
from markdown import markdown
from .exceptions import ValidationError
import bleach

# 自定义的匿名用户
# 无论登录着的用户，还是匿名用户都可以使用current_user.can(), .is_administrator()
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    
    def is_administrator(self):
        return False
# 自定义匿名用戶
login_manager.anonymous_user = AnonymousUser


# 多对多模型，由关系表升级
class Follow(db.Model):
    __tablename__ = 'follows'
    # 关注者 ， 我被谁关注
    fans_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    # 被关注者,我关注哪一用户
    # follower_id follow followed_id
    idol_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    #  该表在数据库中的名字
    __tablename__ = 'users'
    # 结构 primary_key 主键
    # unique 不允许重复
    # index 为列创建索引
    # UserMixin 需要，get_id()
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(64), unique=True, index=True)
    user_name = db.Column(db.String(30), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    
    # 增加一些额外信息，地址、注册日期、最近访问日期、个人信息
    location = db.Column(db.String(64))
    # default可以接受python callable对象
    name = db.Column(db.String(64))
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    about_me = db.Column(db.Text())
    
    avatar_hash = db.Column(db.String(32))
    # role_id 外键， 此列值时role表中的role_id值
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    
    # 在Post类 中反向添加author属性, 一个author多篇文章
    posts = db.relationship('Post', backref='author', lazy="dynamic")
    
    # 若b,c 关注 a  则 a.fans 有 b,c
    # 在follows表中
    # b.idol, c.idol 有a
    #  fans_id   idol_id
    #   b.id       a.id
    #   c.id       a.id
    # 我的关注列表，我是xxx的fans Follow.fans 表示哪一位用户要关注其他用户
    # 回引中lazy="joined",user.idol.all()回返回一个列表，包含所有相应的Follow实例
    # 一次查询，完成操作
    idol = db.relationship('Follow', foreign_keys=[Follow.fans_id],
                             backref=db.backref('fans', lazy='joined'),
                             lazy='dynamic', cascade='all, delete-orphan')
    
    # fans，idol 在“一”的一侧定义，返回“多”的一侧的记录 lazy="dynamic",返回的是查询对象
    # 我的fans列表 我是xxx的idol Follow.idol 表示被关注的用户
    # cascade 父对象上的操作对相关对象的影响， 启动所有默认层叠选项， 删除孤儿记录
    # 删除对象时，默认把对象连接的所有相关对象的外键设为 空， 需求是删除指向该记录的实体
    fans = db.relationship('Follow', foreign_keys=[Follow.idol_id],
                             backref=db.backref('idol', lazy='joined'),
                             lazy='dynamic', cascade='all, delete-orphan')
    
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    
    # 赋予角色属性
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            # 使用admin邮箱注册的user 赋予其admin角色的权限
            if self.email == current_app.config['FLASK_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            # 不是admin邮箱 账户，默认设置其为普通User用户, Role中default字段为True的
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()
        self.follow(self)
    # user转化为json格式，提供给客户端，不需要所有数据
    def to_json(self):
        json_user = {
            'url':url_for('api_bp.get_user', id=self.id),
            'username': self.user_name,
            'last_seen': self.last_seen,
            'post_url': url_for('api_bp.get_user_posts', id=self.id),
            'idol_post_url': url_for("api_bp.get_user_idol_post", id=self.id),
            'post_count': self.posts.count()
        }
        return json_user
    

    # 新建用户时关注自己
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()
    
    # 检验用户是否具有某种权限
    def can(self, perm):
        return self.role is not None and  self.role.has_permission(perm)
    
    def is_administrator(self):
        return self.can(Permission.ADMIN)
        
    def __repr__(self):
        return f'<User {self.user_name}>'

    # 每次都会更新访问时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        # 计算密码散列值
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 生成验证邮箱需要的加密签名
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        # dumps生成的是b‘’字节码， 解码为字符串形式 传入url
        return s.dumps({'confirm':self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True
    
    # 基于令牌的身份验证
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({'id':self.id}).decode('utf-8')
    
    # 验证用户
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return None
        return User.query.get(data['id'])
    
    
    # 重置密码时发送给邮箱的验证
    def generate_password_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id}).decode("utf-8")
    
    # 加密令牌包括用户id信息和新邮件信息
    def generate_change_email_token(self, new_email,expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email':self.id, 'new_email': new_email}).decode('utf-8')
    
    # 查看token内指定的id是否为当前user，是则修改email
    def confirm_new_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        # new_email 是被注册过的邮箱，
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True
    
    
    # 邮件链接处理重置密码，没有用户登录
    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        # 在数据库中查找 id 符合的用户对象
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True
    
    # 使用https://en.gravatar.com/gravatar 生成用户头像
    # size大小， d：没有注册gravatar服务的用户默认图片， r图像级别
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = "https://secure.gravatar.com/avatar"
        else:
            url = 'http://www.gravatar.com/avatar'
        # avatar的hash值 存在时使用存储中（数据库），不存在则新生成一个
        hash = self.avatar_hash or  self.gravatar_hash()
        return f'{url}/{hash}?s={size}&d={default}&r={rating}'
    
    # 生成avatar的hash值
    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    # 关注某一用户
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(fans=self, idol=user)
            db.session.add(f)
    
    # 取消关注
    def unfollow(self, user):
        # User.idol 返回的是查询对象（fans_id=self.id）
        f = self.idol.filter_by(idol_id=user.id).first()
        if f:
            db.session.delete(f)
    # 是否关注某一对象
    def is_following(self, user):
        if user.id is None:
            return False
        return self.idol.filter_by(idol_id=user.id).first() is not None
    
    # 有无user这个fans
    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.fans.filter_by(fans_id=user.id).first() is not None
    
    # 获取所有关注对象的posts
    @property
    def idol_posts(self):
        return Post.query.join(Follow, Follow.idol_id == Post.author_id)\
                .filter(Follow.fans_id == self.id)
    
# 权限
class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16



class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, index=True)
    # 默认角色，用户注册时赋予用户的角色，只有一个为True，其余为FALSE
    default = db.Column(db.Boolean, default=False, index=True)
    # 设置权限
    permissions = db.Column(db.Integer)
    # 关系选项 ‘一’的那端使用relationship,
    # backref在User模型中添加role属性，定义反向关系,可以通过这个属性获取对应Role模型对象
    # 不在通过role_id外键
    # User.query.filter_by(role=first_role)
    users = db.relationship('User', backref='role', lazy='dynamic')
    # role_1.users 返回使用role_1的user对象列表
    def __repr__(self):
        return f'<Role {self.role_name}>'
    
    # 未设置的字段，sqlalchemy会默认设置为None (NULL)
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    
    # 管理角色权限
    def has_permission(self, perm):
        return self.permissions & perm == perm
        
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm
    
    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm
    
    def reset_permission(self):
        self.permissions = 0
    
    # 3种角色 user， moderate， admin
    @staticmethod
    def insert_roles():
        roles = {
            'User' : [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderate' : [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator' : [Permission.FOLLOW, Permission.COMMENT,
                       Permission.WRITE, Permission.MODERATE, Permission.ADMIN]
        }
        default_role = "User"
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            # Role 表中没有对应的3中角色，则添加
            if role is None:
                role = Role(name=r)
                role.reset_permission()
                # 为重置权限后的role添加对应的权限
                # r-> key    [...]->value
            for perm in roles[r]:
                role.add_permission(perm)
            # 默认角色 是user
            role.default = (default_role == role.name)
            db.session.add(role)
        db.session.commit()
    
"""将注册函数load_user传入给flask_login（load_user->self.user_callback）
reload_user时检测根据传入user_id确定的user是否存在（installed），不存在则抛出异常
存在，则为ctx.user
"""
@login_manager.user_loader
# 回调函数需要 根据id 返回一个user对象
def load_user(user_id):
    # 先将传入的字符串转为整数
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    # markdown格式文本转html，缓存
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 由User在Post添加author属性，代表作者
    
    # agument : mapped class
    # backref: indicates the string name of a property to be placed on the related mapper’s class
    # that will handle this relationship in the other direction.
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tag = ['a', 'abbr', 'acronym', 'b', 'blockquote','code', 'em',
                     'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2',
                     'h3', 'p']
        # bleach.linkify: 将url字符串转为html<a>链接
        # bleach.clean 清除html片段中的恶意内容，并返回，tags：允许存在的标签 strip：是否去除不允许的元素
        # markdown 将markdown型式的字符串转为html, output_format :输出格式xhtml（默认）、html
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tag, strip=True))
    # 将内部表示 转为json（http请求和响应的）格式：序列化
    def to_json(self):
        json_port = {
            'url': url_for('api_bp.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'comments_url': url_for('api_bp.get_post_comments', id=self.id),
            'comment_count': self.comments.count(),
            'author_url': url_for('api_bp.get_user', id=self.author_id)
        }
        return json_port
    
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post 没有内容')
        return Post(body=body)
        
# “set”事件监听程序，在body字段设置新的值时，自动调用on_changed_body
# sqlalchemy.event.listen(target, identifier, fn, *args, **kw)
# a string identifier which identifies the event to be intercepted
db.event.listen(Post.body, 'set', Post.on_changed_body)


#评论,与post类似
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 管理员决定是否查禁
    disabled = db.Column(db.Boolean, default=False)
    # 根据User, Post 添加author 和 post属性
    
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tag = ['a', 'abbr', 'acronym', 'b', 'blockquote','code', 'em',
                     'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 'h2',
                     'h3', 'p']
        # bleach.linkify: 将url字符串转为html<a>链接
        # bleach.clean 清除html片段中的恶意内容，并返回，tags：允许存在的标签 strip：是否去除不允许的元素
        # markdown 将markdown型式的字符串转为html, output_format :输出格式xhtml（默认）、html
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tag, strip=True))

    # 将内部表示 转为json（http请求和响应的）格式：序列化
    def to_json(self):
        json_comment = {
            'url': url_for('api_bp.get_comment', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'post_id':  url_for('api_bp.get_post', id=self.post_id),
            'author_url': url_for('api_bp.get_user', id=self.author_id),
        }
        return json_comment

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comments 没有内容')
        return Comment(body=body)
    
db.event.listen(Comment.body, 'set', Comment.on_changed_body)
