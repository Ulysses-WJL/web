"""测试客户端，复现应用运行在web服务器中的环境"""
import unittest
from app import db, create_app
from app.models import User, Role

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        # Create an :class:`~flask.ctx.AppContext`
        # 返回AppContext对象
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        # 添加Flask测试客户端对象Creates a test client for this application
        # use_cookies 让客户端像浏览器一样使用cookie
        self.client = self.app.test_client(use_cookies=True)
    
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_home_page(self):
        """测试首页"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Stranger" in response.get_data(as_text=True))
    
    def test_register_login_out(self):
        response = self.client.post('/auth/register', data={'email':'register@test.com',
                                                            'username':'register',
                                                            'password':'123',
                                                            'password2':'123'})
        self.assertEqual(response.status_code, 302)
        