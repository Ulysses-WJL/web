"""
登录表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from ..models import User

class LoginForm(FlaskForm):
    # 邮件登录， 非空，长度1-64， email格式
    email = StringField(
        '邮箱', validators=[
            DataRequired(), Length(
                1, 64), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我- _ -')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(),
            Length(
                1,
                64)])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][a-zA-Z0-9_.]*$', 0,
        '用户名由字母、数字、下划线或.构成')])
    password = PasswordField(
        '密码',
        validators=[
            DataRequired(),
            EqualTo(
                'password2',
                message='两次输入的密码要一致')])

    password2 = PasswordField('再次输入密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('此邮件已注册')
    
    def validate_username(self, field):
        if User.query.filter_by(user_name=field.data).first():
            raise ValidationError('此用户名已存在')
    


class ChangePasswordForm(FlaskForm):
    password_old = PasswordField('请输入原始密码', validators=[DataRequired()])
    password_new1 = PasswordField(
        '请输入新密码',
        validators=[DataRequired(),
                    EqualTo('password_new2', message='两次输入的密码要一致')])
    password_new2 = PasswordField('请确认新密码', validators=[DataRequired()])
    submit = SubmitField('确定')



class ChangeUserNameForm(FlaskForm):
    username_new = StringField(
        '请输入新的用户名',
        validators=[
            DataRequired(), Length(1, 64),
            Regexp('^[A-Za-z][a-zA-Z0-9_.]*$', 0,'用户名由字母、数字、下划线或.构成')])
    submit = SubmitField('确认修改')


class ForgetPasswordForm(FlaskForm):
    email = StringField('绑定邮箱', validators=[DataRequired(), Email(), Length(1, 64)])
    username = StringField('用户名', validators=[DataRequired()])
    submit = SubmitField('确认重置密码')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('请再次输入密码', validators=[DataRequired()])
    submit = SubmitField('重置密码')

class ChangeEmailForm(FlaskForm):
    email = StringField('更换邮箱', validators=[DataRequired(), Email(), Length(1, 64)])
    password = PasswordField('输入密码', validators=[DataRequired()])
    submit = SubmitField('确认更换')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')