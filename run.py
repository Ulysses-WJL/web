import os
from app import create_app, db
from app.models import User, Role

#app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
app = create_app('default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)

@app.cli.command()
def test():
    """Run the unit tests"""
    import unittest
    tests = unittest.TestLoader().discover('test')
    unittest.TextTestRunner(verbosity=2).run(tests)