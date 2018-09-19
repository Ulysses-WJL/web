import unittest
from app.models import User
import time
from  app import db

class UserModelTest(unittest.TestCase):
    def test_password_setter(self):
        u = User(password='123')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verify(self):
        u = User(password='monkey')
        self.assertTrue(u.verify_password('monkey'))
        self.assertFalse(u.verify_password('cat'))
    
    def test_password_random(self):
        u1 = User(password='cat')
        u2 = User(password='cat')
        self.assertFalse(u1.password_hash==u2.password_hash)
    
    def test_valid_comfirmation_token(self):
        u_1 = User(password='123456')
        token_1 = u_1.generate_confirmation_token()
        self.assertTrue(u_1.confirm(token_1))
    
    def test_invalid_comfirmation_token(self):
        u_1 = User(password='123456')
        u_2 = User(password='123')
        print(f"id1:{u_1.id}\nid2:{u_2.id}")
        db.session.add(u_1)
        db.session.add(u_2)
        db.session.commit()
        
        token_1 = u_1.generate_confirmation_token()
        self.assertFalse(u_2.confirm(token_1))
    
    def test_expired_comfirmation_token(self):
        u_1 = User(password='123456')
        token_1 = u_1.generate_confirmation_token(3)
        time.sleep(5)
        self.assertFalse(u_1.confirm(token_1))