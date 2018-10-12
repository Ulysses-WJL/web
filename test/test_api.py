"""api 测试"""
import unittest
from app.models import User, Permission, Role, Post, Comment
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
        """返回多数API请求要发送的通用首部
        PUT /api/v1/posts/5 HTTP/1.1
        Host: 127.0.0.1:5000
        Authorization: Basic amlhbmxpYW5nd3UxMTcxQGdtYWlsLmNvbToxMjM=
        Content-Type: application/json
        Cache-Control: no-cache
        Postman-Token: d972e7ae-a2b8-2152-b3e1-7f60196ab9b4
        
        {
            "body":"new body"
        }
        """
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
        # 用json.dumps()对主体进行编码成JSON格式
        response = self.client.post('/api/v1/posts/',
                                    headers=self.get_api_headers('apipost@test.com','123'),
                                    data=json.dumps({'body':''}))
        self.assertEqual(400, response.status_code)
        
        response = self.client.post('/api/v1/posts/',
                                    headers=self.get_api_headers('apipost@test.com','123'),
                                    data=json.dumps({'body':'new *post*'}))
        self.assertEqual(201, response.status_code)
        # 新生成的post 的url
        url = response.headers.get('Location')
        self.assertIsNotNone(url)
        # 通过url获取刚刚获得post
        response = self.client.get(url, headers=self.get_api_headers('apipost@test.com','123'))
        self.assertTrue(200, response.status_code)
        # 将json格式的内容转为python dict
        json_response = json.loads(response.get_data(as_text=True))
       
        self.assertEqual('http://localhost'+json_response.get('url'), url)
        self.assertEqual('new *post*', json_response['body'])
        self.assertEqual('<p>new <em>post</em></p>', json_response['body_html'])
        json_post = json_response
        
        # 根据用户获取posts
        response = self.client.get(f'/api/v1/users/{u.id}/posts/',
                                   headers=self.get_api_headers('apipost@test.com', '123'))
        self.assertEqual(200, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(1, json_response.get('posts_count', 0))
        self.assertIsNotNone(json_response.get('posts'))
        # 最近的post，即刚刚生成的post
        self.assertEqual(json_post, json_response['posts'][0])
        
        # 用户关注对象的posts
        response = self.client.get(f'/api/v1/users/{u.id}/timeline/',
                                   headers=self.get_api_headers('apipost@test.com', '123'))
        self.assertEqual(200, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(1, json_response.get('posts_count'))
        self.assertEqual(json_post, json_response['posts'][0])
        
        # 修改post
        response = self.client.put(url,
                                   headers=self.get_api_headers('apipost@test.com', '123'),
                                   data=json.dumps({'body':'new new post'}))
        self.assertEqual(200, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('new new post', json_response['body'])
        self.assertEqual(url, 'http://localhost'+json_response['url'])
        self.assertEqual('<p>new new post</p>', json_response['body_html'])
        
    def test_user(self):
        """测试user的方法"""
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(role=r, email='user1@test.com', password='123',
                 confirmed=True, user_name='user1')
        u2 = User(role=r, email='user2@test.com', password='123',
                 confirmed=True, user_name='user2')
        db.session.add_all([u1, u2])
        db.session.commit()
        
        # 获取user对象
        response = self.client.get(f'/api/v1/users/{u1.id}',
                                   headers=self.get_api_headers('user1@test.com', '123'))
        self.assertEqual(200, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('user1', json_response['username'])
        
        response = self.client.get(f'/api/v1/users/{u2.id}',
                                   headers=self.get_api_headers('user2@test.com', '123'))
        self.assertEqual(200, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('user2', json_response['username'])
        
    def test_comment(self):
        """评论"""
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u1 = User(role=r, user_name='test_comment1', confirmed=True,
                 email='test_comment1@test.com', tpassword='123')
        u2 = User(role=r, user_name='test_comment2', confirmed=True,
                 email='test_comment2@test.com', password='123')
        db.session.add_all([u1, u2])
        db.session.commit()
        # 生成post
        post = Post(author=u1, body='post u1')
        db.session.add(post)
        db.session.commit()
        # 给新生成的post添加评论
        response = self.client.post(f'/api/v1/posts/{post.id}/comments/',
                                    headers=self.get_api_headers('test_comment1@test.com', '123'),
                                    data=json.dumps({'body':'test comment 1'}))
        self.assertTrue(201, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        for k in json_response:
            print(k, json_response[k])
        self.assertEqual('test comment 1', json_response['body'])
        url = response.headers.get('Location')
        self.assertIsNotNone(url)
        
        # 获取新生成的评论 /api/v1/posts/comments/1
        response = self.client.get(url,
                                   headers=self.get_api_headers('test_comment1@test.com', '123'))
        self.assertTrue(200, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        print(url)
        self.assertEqual(url, 'http://localhost'+json_response['url'])
        self.assertEqual('test comment 1', json_response['body'])
        
        # 再添加新的评论
        comment = Comment(body='add new comment',author=u2, post=post)
        db.session.add(comment)
        db.session.commit()
        # 获取新评论
        response = self.client.get(f'/api/v1/posts/{post.id}/comments/',
                                   headers=self.get_api_headers('test_comment2@test.com', '123'))
        self.assertEqual(200, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        # comments列表
        self.assertIsNotNone(json_response.get('comments'))
        self.assertEqual(2, json_response.get('count', 0))
        
        response = self.client.get('/api/v1/comments/',
                                   headers=self.get_api_headers('test_comment2@test.com', '123'))
        self.assertTrue(200, response.status_code)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('comments'))
        self.assertEqual(2, json_response.get('comments_count', 0))
        