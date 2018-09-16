from flask import current_app
from flask_migrate import Migrate, MigrateCommand #载入migrate扩展
from app import db
from app.models import Role, User
from flask_script import Manager, Shell

app = current_app._get_current_object()
migrate = Migrate(current_app, db)  #注册migrate到flask
manager = Manager(current_app)

manager.add_command('db', MigrateCommand) #在终端环境下添加一个db命令

if __name__ == '__main__':
    manager.run()