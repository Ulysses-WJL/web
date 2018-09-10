from flask import render_template, Flask, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class NameForm(FlaskForm):
    # validators:验证器
    # DataRequired： Checks the field's data is 'truthy' otherwise stops the validation chain.
    # 确保类型转换后字段中有数据
    
    # StringField :represents an ``<input type="text">``.
    # 表示属性为 type='text'的HTML<input>元素， 文本字段
    
    name = StringField('What is your name?', validators=[DataRequired()])
    # 代表属性为 type='submit'的HTML输入， 表单提交按钮
    submit = SubmitField("Submit")
    
app = Flask(__name__)
bootstarp = Bootstrap(app)
moment = Moment(app)
# 配置flask-wtf 秘钥
app.config['SECRET_KEY'] = 'secret key'

@app.route('/')
def index():
    # 渲染模板
    return render_template('index.html', url=url_for('static',filename='favicron.ico'),
                           current_time=datetime.utcnow())
    # 静态文件

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
