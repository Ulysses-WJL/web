import os
from flask import render_template, Flask, url_for,session, redirect, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
bootstarp = Bootstrap(app)
moment = Moment(app)
# 配置flask-wtf 秘钥
app.config['SECRET_KEY'] = 'secret key'
# 数据库所在url,配置到flask的设置中
DBNAME = 'sqltest'
URL = f'mysql+pymysql://root:62300313@localhost:3306/{DBNAME}'
app.config['SQLALCHEMY_DATABASE_URI'] = URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# flask_sqlalchemy 封装了 sqlalchemy的功能
db = SQLAlchemy(app)

# 数据库中的2个表 映射为 python类
class User(db.Model):
    #  该表在数据库中的名字
    __tablename__ = 'users'
    # 结构 primary_key 主键
    # unique 不允许重复
    # index 为列创建索引
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String, unique=True, index=True)
    pass_wd = db.Column(db.String)
    # role_id 外键
    role_id = db.Column(db.Integer, db.ForeignKey('role.role_id'))
    
    def __repr__(self):
        return f'<User {self.user_name}>'

class Role(db.Model):
    __tablename__ = 'role'
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String, unique=True, index=True)
    # 关系选项 ‘一’的那端使用relationship
    users = db.relationship('User', backref='role')
    def __repr__(self):
        return f'<Role {self.role_name}>'

# 表单类
class NameForm(FlaskForm):
    # validators:验证器
    # DataRequired： Checks the field's data is 'truthy' otherwise stops the validation chain.
    # 确保类型转换后字段中有数据, InputRequired 转换前字段有数据
    
    # StringField :represents an ``<input type="text">``.
    # 表示属性为 type='text'的HTML<input>元素， 文本字段
  
    name = StringField('What is your name?', validators=[DataRequired()])
    # 代表属性为 type='submit'的HTML输入， 表单提交按钮
    # 第一个参数是把表单渲染成html时的使用的标注label
    submit = SubmitField("Submit")
    


@app.route('/', methods=['GET', 'POST'])
def index():
    # name = None
    form = NameForm()
    # Call :meth:`validate` only if the form is submitted.
    #  This is a shortcut for ``form.is_submitted() and form.validate()``.
    # 当表单被提交时，调用验证函数， 返回 是否提交了表单&内容是否为空
    if form.validate_on_submit():
        # name = form.name.data # 表单的数据，空则为''
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('更改了用户名！')
        session['name'] = form.name.data
        return redirect(url_for('index')) # 提交数据后，回到index页面，数据被保存在session中
        # form.name.data = ''
    # 渲染模板
    return render_template('index.html', url=url_for('static',filename='favicron.ico'),form=form,name=session.get('name'),
                           current_time=datetime.utcnow())
    # 静态文件favicron.ico

@app.route('/user/<name>')
def hello(name=None):
    return render_template('user.html', name=name, url=url_for("hello",name=name, _external=True),
                           users=[{'name': 'jhon'},
                                  {'name': 'Tom'},
                                  {'name': 'jack'},
                                  {'name': 'ulysses'},
                                  {'name': 'frank'}],
                           current_time=datetime.utcnow())
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, port=8888)
