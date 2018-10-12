"""
使用selenium测试
"""
import threading
import time
import re
from selenium import webdriver
from unittest import TestCase
from app import create_app, db, fake
from app.models import Role, User, Post, Comment

class SeleniumTestCase(TestCase):
    client = None
    
    @classmethod
    # 在类中所有测试完成之前，之后
    def setUpClass(cls):
        # 使用webdriver API启动chrome实例
        options = webdriver.ChromeOptions()
        # 给浏览器添加参数, 不启动浏览器界面
        options.add_argument('headless')
        try:
            # Creates a new instance of the chrome driver
            cls.client = webdriver.Chrome(options=options)
        except:
            pass
        # 浏览器没有启动时，跳过这些测试
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
            
            # 在一个子线程中启动Flask服务器， app.run()
            cls.server_thread = threading.Thread(
                #'use_reloader', 'use_debugger'默认设置为和'debug'相同的值, self.debug = bool(debug)
                target=cls.app.run, kwargs={"debug": False})
            cls.server_thread.start()
            time.sleep(1)
            
    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # 关闭flask服务器和浏览器
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()
            db.drop_all()
            db.session.remove()
            cls.app_context.pop()
    
    def setUp(self):
        if not self.client:
            self.skipTest('没有浏览器')

    
    def tearDown(self):
        pass
        
    def test_admin_home_page(self):
        # 进入首页
        # 添加admin用户
        admin_role = Role.query.filter_by(name='Administrator').first()
        admin = User(role=admin_role, user_name='admin_1', confirmed=True,
                     email='admin_1@test.com', password='cat')
        db.session.add(admin)
        db.session.commit()
        self.client.get('http://localhost:5000/')
        # Gets the source of the current page
        self.assertTrue(re.search('Hello,\s+Stranger', self.client.page_source))
        # 定位UI元素
        #     ID = "id"
        #     XPATH = "xpath"
        #     LINK_TEXT = "link text"
        #     PARTIAL_LINK_TEXT = "partial link text"
        #     NAME = "name"
        #     TAG_NAME = "tag name"
        #     CLASS_NAME = "class name"
        #     CSS_SELECTOR = "css selector"
        # = find_element(by=BY.LINK_TEXT, '登录') <a href="{{ url_for('auth_bp.login') }}">登录</a>
        self.client.find_element_by_link_text('登录').click()
        # 在浏览器中触发一次点击
        self.assertIn('<h1>登录</h1>', self.client.page_source)
        
        # 登录
        # file_input = driver.find_element_by_name('profilePic')
        # file_input.send_keys("path/to/profilepic.gif")
        self.client.find_element_by_name('email').clear()
        self.client.find_element_by_name('email').send_keys('admin_1@test.com')
        self.client.find_element_by_name('password').clear()
        self.client.find_element_by_name('password').send_keys('cat')
        time.sleep(1)
        self.client.find_element_by_name('submit').click()
        time.sleep(1)
        self.assertTrue(re.search('Hello,\s+admin_1', self.client.page_source))
        
        # 个人信息界面
        self.client.find_element_by_link_text('个人信息').click()
        self.assertTrue(re.search('<h1>admin_1</h1>', self.client.page_source))
        
            
            