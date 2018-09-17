import unittest
from app.models import User

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