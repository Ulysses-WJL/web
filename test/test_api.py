"""api 测试"""
import unittest
from app.models import User, Permission, Role
from app import db, create_app
from base64 import b64encode
from flask import url_for
import json

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def get_api_headers(self, username, password):
        """返回多数API请求要发送的通用首部"""
        return {
            'Authorization':'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def test_no_auth(self):
        """未登陆的请求posts"""
        response = self.client.get('/api/v1/posts/', content_type='application/json')
        self.assertEqual(401, response.status_code)
    
    def test_404(self):
        """错误的URL， 404"""
        response = self.client.get('/api/v1/wrong/url', headers=self.get_api_headers('email', 'password'))
        self.assertTrue(404, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('not found', json_response['error'])
    
    def test_bad_auth(self):
        """错误的密码进行登录"""
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True,
                 role=r)
        db.session.add(u)
        db.session.commit()

        # authenticate with bad password
        response = self.client.get(
            '/api/v1/posts/',
            headers=self.get_api_headers('john@example.com', 'dog'))
        self.assertEqual(response.status_code, 401)
    
    def test_anonymous(self):
        """匿名用户"""
        response = self.client.get('api/v1/posts/',
                                   headers=self.get_api_headers('',''))
        self.assertEqual(401, response.status_code)
        
    def test_token_auth(self):
        """使用令牌token代替邮箱密码登录"""
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True,
                 role=r)
        db.session.add(u)
        db.session.commit()

        # issue a request with a bad token
        response = self.client.get(
            '/api/v1/posts/',
            headers=self.get_api_headers('bad-token', ''))
        self.assertEqual(response.status_code, 401)

        # get a token
        response = self.client.post(
            '/api/v1/tokens/',
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']

        # issue a request with the token
        response = self.client.get(
            '/api/v1/posts/',
            headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

    def test_unconfirmed_account(self):
        """注册、但未验证的用户"""
        r = Role.query.filter_by(name="User").first()
        self.assertIsNotNone(r)
        u = User(email='unconfirmed@test.com', password='123',
                 role=r, confirmed=False)
        db.session.add(u)
        db.session.commit()
        
        response = self.client.get('/api/v1/posts/',
                                   headers=self.get_api_headers('unconfirmed@test.com', '123'))
        self.assertEqual(403, response.status_code)
    
    def test_posts(self):
        # 创建用户
        r = Role.query.filter_by(name='Administrator').first()
        self.assertIsNotNone(r)
        u = User(email='apipost@test.com', password='123', role=r, confirmed=True)
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.can(Permission.WRITE))
        # 写一篇文章
        response = self.client.post('/api/v1/posts/',
                                    headers=self.get_api_headers('apipost@test.com','123'),
                                    data=json.dumps({'body':''}))
        self.assertEqual(400, response.status_code)
        
        response = self.client.post('/api/v1/posts/',
                                    headers=self.get_api_headers('apipost@test.com','123'),
                                    data=json.dumps({'body':'new *post*'}))
        self.assertEqual(201, response.status_code)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)
        # 通过url获取刚刚获得post
        response = self.client.get(url, headers=self.get_api_headers('apipost@test.com','123'))
        self.assertTrue(200, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
       
        self.assertEqual('http://localhost'+json_response.get('url'), url)
        self.assertEqual('new *post*', json_response['body'])
        self.assertEqual('<p>new <em>post</em></p>', json_response['body_html'])
        