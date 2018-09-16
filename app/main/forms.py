from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
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