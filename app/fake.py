"""生成虚拟用户和虚拟blog"""
from random import randint
from faker import Faker
from sqlalchemy.exc import IntegrityError
from . import db
from .models import User, Post

# 随机生成用户
def users(count=100):
    fake = Faker()
    i = 0
    while i < count:
        # 由Faker 随机生成数据
        u = User(email=fake.email(),
                 user_name=fake.user_name(),
                 password = '123456',
                 location = fake.city(),
                 confirmed=True,
                 name = fake.name(),
                 about_me = fake.text(),
                 member_since = fake.past_date())
        db.session.add(u)
        # user_name, email 是唯一的
        # 若随机产生的信息出现重复，则数据库报错，回滚
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            # 添加到数据库会话中的对象都会恢复到它们曾经在数据库中的状态
            db.session.rollback()

# 随机生成blog
def posts(count=100):
    fake = Faker()
    i = 0
    user_count = User.query.count()
    for i  in range(count):
        # 随机 偏移 选择一个用户生成post
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(author=u, body=fake.text(),
                 timestamp=fake.past_date())
        db.session.add(p)
    db.session.commit()
        