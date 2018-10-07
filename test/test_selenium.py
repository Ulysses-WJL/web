"""
使用selenium测试
"""
from selenium import webdriver
from unittest import TestCase
from app import create_app, db
from app.models import Role, User, Post, Comment
from app import fake
import threading
class SeleniumTestCase(TestCase):
    client = None
    
    @classmethod
    def setUpClass(cls):
        # 启动chrome
        options = webdriver.ChromeOptions()
        # 给浏览器添加参数
        options.add_argument('headless')
        try:
            # Creates a new instance of the chrome driver
            cls.client = webdriver.Chrome(chrome_options=options)
        except:
            pass
        if cls.client:
            # 创建应用
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()
            
            # 只有错误信息会被输出
            import logging
            # 创建logger
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")
            
            db.create_all()
            Role.insert_roles()
            fake.users(10)
            fake.posts(10)
            
            # 添加admin用户
            admin_role = Role.query.filter_by(name='Administrator')
            admin = User(role=admin_role, user_name='admin', confirmed=True,
                         email='admin@test.com', password='123')
            db.session.add(admin)
            db.session.commit()
            
            # 在一个线程中启动Flask服务器
            cls.server_thread = threading.Thread(
                target=cls.app.run, kwargs={"debug": "true", 'use_reloader':True,
                                            'user_debugger':True})
            cls.server_thread.start()
            
    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # 关闭flask服务器和浏览器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()
            # 删除数据库
            db.session.remove()
            db.drop_all()
            
            cls.app_context.pop()
    
    def setUp(self):
        if not self.client:
            self.skipTest('没有浏览器')
    
    def tearDown(self):
        pass
        
            
            
            