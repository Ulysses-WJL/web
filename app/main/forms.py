from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Regexp, Email, ValidationError
from ..models import Role, User
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


class EditProfileForm(FlaskForm):
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    about_me = TextAreaField('个人信息')
    submit = SubmitField('提交')

class EditProfileAdminForm(FlaskForm):
    user_name = StringField('用户名', validators=[DataRequired(), Length(1, 64),
                                               Regexp('^[A-Za-z][a-zA-Z0-9_.]*$',
                                                      0,'用户名由字母、数字、下划线或.构成')])
    confirmed = BooleanField('是否被验证')
    role = SelectField('角色', coerce=int)
    email = StringField(
        '邮箱',
        validators=[
            DataRequired(),
            Email(),
            Length(
                1,
                64)])
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('地址', validators=[Length(0, 64)])
    about_me = TextAreaField('个人信息')
    submit = SubmitField('提交')
    
    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        # 实现SelectField实例的choices属性，需要包含(选项标识符, 显示的文本字符串)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.id).all()]
        self.user = user
    
    def validate_email(self, field):
        # 修改邮箱，而此邮箱已存在
        if field.data != self.user.email and\
                User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已存在')
    
    def validate_user_name(self, field):
        if field.data != self.user.user_name and\
            User.query.filter_by(user_name=field.data).first():
            raise  ValidationError('此用户名已被注册')

class PostForm(FlaskForm):
    body = TextAreaField('what you want to say:', validators=[DataRequired()])
    submit = SubmitField('确认')