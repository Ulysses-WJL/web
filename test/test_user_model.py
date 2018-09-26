import unittest
from app.models import User, Permission, Follow, Role, AnonymousUser
import time
from app import db, create_app
from datetime import datetime


class UserModelTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    # 设置密码
    def test_password_setter(self):
        u = User(password='123')
        self.assertTrue(u.password_hash is not None)

    # 读取密码
    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    # 2个不同的密码，token值
    def test_password_verify(self):
        u = User(password='monkey')
        self.assertTrue(u.verify_password('monkey'))
        self.assertFalse(u.verify_password('cat'))

    # 相同密码加盐
    def test_password_random(self):
        u1 = User(password='cat')
        u2 = User(password='cat')
        self.assertFalse(u1.password_hash == u2.password_hash)

    # 修改密码，验证token中id
    def test_valid_confirmation_token(self):
        u_1 = User(password='123456')
        token_1 = u_1.generate_confirmation_token()
        self.assertTrue(u_1.confirm(token_1))

    # 2个不同user的token验证不正确
    def test_invalid_confirmation_token(self):
        u_1 = User(password='123456')
        u_2 = User(password='123')
        print(f"id1:{u_1.id}\nid2:{u_2.id}")
        db.session.add(u_1)
        db.session.add(u_2)
        db.session.commit()

        token_1 = u_1.generate_confirmation_token()
        self.assertFalse(u_2.confirm(token_1))

    # token 时效性
    def test_expired_confirmation_token(self):
        u_1 = User(password='123456')
        token_1 = u_1.generate_confirmation_token(3)
        time.sleep(5)
        self.assertFalse(u_1.confirm(token_1))
    
    # 重置密码时
    def test_valid_reset_password(self):
        u1 = User(password='123')
        db.session.add(u1)
        db.session.commit()
        token = u1.generate_password_token()
        self.assertTrue(User.reset_password(token,'cat'))
        self.assertTrue(u1.verify_password('cat'))

    def test_invalid_reset_password(self):
        u1 = User(password='123')
        db.session.add(u1)
        db.session.commit()
        token = u1.generate_password_token()
        self.assertFalse(User.reset_password(token+'4','cat'))
        self.assertTrue(u1.verify_password('123'))

    # 修改用户邮箱
    def test_valid_change_email(self):
        u1 = User(password='123', email="test1@qq.com")
        db.session.add(u1)
        db.session.commit()
        token = u1.generate_change_email_token('test1@gmail.com')
        self.assertTrue(u1.confirm_new_email(token))
        self.assertTrue(u1.email=='test1@gmail.com')

    def test_invalid_change_email(self):
        u1 = User(password='123', email="test2@qq.com")
        u2 = User(password='123', email="test3@qq.com")
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_change_email_token('test4@gmail.com')
        self.assertFalse(u2.confirm_new_email(token))
        self.assertTrue(u2.email=='test3@qq.com')
    
    # 替换的邮箱已存在
    def test_duplicate_change_email(self):
        u1 = User(email='john@qq.com', password='cat')
        u2 = User(email='susan@qq.org', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u2.generate_change_email_token('john@qq.com')
        self.assertFalse(u2.confirm_new_email(token))
        self.assertTrue(u2.email == 'susan@qq.org')
    
    # 测试角色属性 default
    def test_user_role(self):
        u1 = User(email='test_user@example.com',password='123')
        self.assertTrue(u1.can(Permission.FOLLOW))
        self.assertTrue(u1.can(Permission.COMMENT))
        self.assertTrue(u1.can(Permission.WRITE))
        self.assertFalse(u1.can(Permission.MODERATE))
        self.assertFalse(u1.can(Permission.ADMIN))
    
    #
    def test_moderate_role(self):
        r = Role.query.filter_by(name='Moderate').first()
        u1 = User(email='test_moderate@qq.com', password='123', role=r)
        self.assertTrue(u1.can(Permission.FOLLOW))
        self.assertTrue(u1.can(Permission.COMMENT))
        self.assertTrue(u1.can(Permission.WRITE))
        self.assertTrue(u1.can(Permission.MODERATE))
        self.assertFalse(u1.can(Permission.ADMIN))
       
    def test_admin_role(self):
        r = Role.query.filter_by(name='Administrator').first()
        u1 = User(email='test_moderate@qq.com', password='123', role=r)
        self.assertTrue(u1.can(Permission.FOLLOW))
        self.assertTrue(u1.can(Permission.COMMENT))
        self.assertTrue(u1.can(Permission.WRITE))
        self.assertTrue(u1.can(Permission.MODERATE))
        self.assertTrue(u1.can(Permission.ADMIN))

    # 匿名用户属性
    def test_anonymous_role(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))
    
    # last-seen
    def test_user_last_seen(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        now = datetime.utcnow()
        print(f'now:{now}\n'
              f'member_since:{u.member_since}')
        self.assertTrue(
            (datetime.utcnow() - u.member_since).total_seconds() < 3)
        self.assertTrue(
            (datetime.utcnow() - u.last_seen).total_seconds() < 3)
        
    # 访问时间
    def test_ping(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        time.sleep(3)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)
    
    # 测试avatar头像生成
    def test_gravatar(self):
        u = User(password='123', email='avatar@test.com')
        with self.app.test_request_context('/'):
            gravatar = u.gravatar()
            gravatar_128 = u.gravatar(size=128)
            gravatar_pg = u.gravatar(rating='pg')
            gravatar_retro = u.gravatar(default='retro')
            # print(f"hash:{gravatar}")
            # print(f"hash:{u.avatar_hash}")
            self.assertTrue('http://www.gravatar.com/avatar/' +
                            'd648ea7ebc8127250f7ad525f35dac3f' in gravatar)
            self.assertTrue('s=128' in gravatar_128)
            self.assertTrue('r=pg' in gravatar_pg)
            self.assertTrue('d=retro' in gravatar_retro)
    
    # 关注功能
    def test_follow(self):
        u1 = User(password='123', email='u1@test.com')
        u2 = User(password='123', email='u2@test.com')
        db.session.add_all([u1, u2])
        db.session.commit()
        self.assertFalse(u1.is_followed_by(u2))
        self.assertFalse(u1.is_following(u2))
        timestamp_before = datetime.utcnow()
        print(f'time_before:{timestamp_before}\n')
        # u1关注u2
        u1.follow(u2)
        db.session.add(u1)
        db.session.commit()
        timestamp_after = datetime.utcnow()
        print(f'time_after:{timestamp_after}\n')
        # 关注 正确
        self.assertTrue(u1.is_following(u2))
        self.assertTrue(u2.is_followed_by(u1))
        self.assertFalse(u1.is_followed_by(u2))
        self.assertFalse(u2.is_following(u1))
        # fans ,idol 属性正确
        self.assertTrue(u1.idol.count()==1)
        self.assertTrue(u2.fans.count()==1)
        
        # follow 端的fans 和 idol 属性正确性
        f = u1.idol.all()[-1]
        self.assertTrue(f.idol == u2)
        print(f'time:{f.timestamp}\n')
        self.assertTrue(timestamp_before <= f.timestamp )
        f = u2.fans.all()[-1]
        self.assertTrue(f.fans == u1)
        
        # 取消关注
        u1.unfollow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.idol.count() == 0)
        self.assertTrue(u2.fans.count() == 0)
        self.assertTrue(Follow.query.count() == 0)
        
        # 对象被删除时，Follow表中对应记录要被删除
        u2.follow(u1)
        db.session.add_all([u1, u2])
        db.session.commit()
        db.session.delete(u2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 0)