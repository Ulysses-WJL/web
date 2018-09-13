from flask_migrate import Migrate, MigrateCommand #载入migrate扩展
from app import app, db
from app.models import Role, User
from flask_script import Manager, Shell
migrate = Migrate(app, db)  #注册migrate到flask
manager = Manager(app)

manager.add_command('db', MigrateCommand) #在终端环境下添加一个db命令

if __name__ == '__main__':
    manager.run()