import os
import click
import sys
from app import create_app, db
from app.models import User, Role,Post, Follow, Permission
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
#app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
app = create_app('default')
migrate = Migrate(app, db)
    
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Post=Post, Follow=Follow, Permission=Permission)


COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()
@app.cli.command()
@click.option('--coverage/--no-coverage', default=False,
              help='Run tests under code coverage')
def test(coverage):
    """Run the unit tests"""
    if coverage and not os.environ.get("FLASK_COVERAGE"):
        os.environ['FLASK_COVERAGE'] = '1'
        # 重启脚本，设置了FLASK_COVERAGE，启动覆盖检测
        print('Reset')
        # .executable:python可执行文件路径
        # 执行可执行文件
        os.execvp(sys.executable, [sys.executable]+sys.argv)
    print(f'Executable file:{sys.executable}\n'
          f'args:{sys.argv}')
    import unittest
    tests = unittest.TestLoader().discover('test')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        COV.report()
        # basedir = os.path.abspath(os.path.dirname(__file__))
        # covdir = os.path.join(basedir, 'COV-html')
        COV.html_report(directory='COV-html')
        # print(f"HTML version: file://{covdir}/index.html")
        COV.erase()
    