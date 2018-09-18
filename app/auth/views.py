from flask import render_template, redirect, request, url_for, flash
from . import auth_bp
from flask_login import login_required, login_user, logout_user, current_user
from ..models import User
from .form import LoginForm, RegistrationForm
from .. import db
from ..email import send_email


@auth_bp.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    # 请求类型GET，直接进行渲染模板
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            # 传入一个实际的user， 默认remember=False
            # id被以字符串形式写入会话session， _request_ctx_stack.top.user = user
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main_bp.index')
            return redirect(next)
        # 密码错误或没有这个user时闪现消息
        flash('密码或邮箱错误')
    return render_template('auth/login.html', form=form)

# login_required 保护路由


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('main_bp.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            user_name=form.username.data,
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        # to, subject, template, **kwargs
        send_email(user.email, '确认邮箱', 'auth/email/confirm', user=user, token=token)
        flash('已发验证信息到注册邮箱')
        # 注册完成 进入登录界面
        return redirect(url_for('main_bp.index'))
    # 注册界面
    return render_template('auth/register.html', form=form)

# 用户点击验证链接后的处理函数
# 受保护的路由，需要登录
@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        #  是已经验证过的用户，直接进入主页面
        return redirect(url_for('main_bp.index'))
    if current_user.confirm(token):
        # 验证token成功， add后 commit提交
        db.session.commit()
        flash('验证成功，可正常登录使用！')
    else:
        flash('验证未能通过， 链接无效或失去时效')
    # 验证失败或成功，都回到主页面
    return redirect('main_bp.index')