from flask import render_template, redirect, request, url_for, flash
from . import auth_bp
from flask_login import login_required, login_user, logout_user
from ..models import User
from .form import LoginForm

@auth_bp.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    # 请求类型GET，直接进行渲染模板
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data) :
            # 传入一个实际的user， 默认remember=False
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startwith('/'):
                next = url_for('main_bp.index')
            return redirect(next)
        # 密码错误或没有这个user时闪现消息
        flash('Invalid user name or password')
    return render_template('auth/login.html', form=form)

# login_required 保护路由
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('main_bp.index'))
