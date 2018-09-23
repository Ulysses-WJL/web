from flask import render_template, redirect, request, url_for, flash
from . import auth_bp
from flask_login import login_required, login_user, logout_user, current_user
from ..models import User
from .form import LoginForm, RegistrationForm, ChangePasswordForm, ChangeUserNameForm,\
    ResetPasswordForm, ForgetPasswordForm, ChangeEmailForm
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
                next = url_for('main_bp.index', _external=True)
            return redirect(next)
        # 密码错误或没有这个user时闪现消息
        flash('密码或邮箱错误')
    return render_template('auth/login.html', form=form)



# login_required 保护路由
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出')
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
    return redirect(url_for('main_bp.index'))


@auth_bp.before_app_request
def before_request():
    """已登录，但账户未验证，请求的url不在身份验证蓝本中，
    也不是对静态文件的请求。此条件下，拦截请求，重定向到一个确认账户相关信息的页面"""
    if current_user.is_authenticated:
        # 每次请求前执行刷新访问时间
        current_user.ping()
        if not current_user.confirmed \
            and request.blueprint != 'auth_bp' \
            and request.endpoint != 'static' :
            return redirect(url_for('auth_bp.unconfirmed'))


# 未验证的需要重新发邮件验证， 验证过的，回到主页面
@auth_bp.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main_bp.index'))
    # 返回未确认页面
    return render_template('auth/unconfirmed.html')


#重新发送验证邮件
@auth_bp.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '确认邮箱', 'auth/email/confirm', user=current_user, token=token)
    flash('已经再次发送验证邮件，请接收')
    return redirect('main_bp.index')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password_old.data):
            current_user.password = form.password_new1.data
            db.session.add(current_user)
            db.session.commit()
            flash('已修改密码，请重新登录')
            logout_user()
            return redirect(url_for('main_bp.index'))
        else:
            flash('修改密码失败，请确认原密码是否正确')
    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/change-username', methods=['GET', 'POST'])
@login_required
def change_username():
    form = ChangeUserNameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_name=form.username_new.data).first()
        if user is None:
            current_user.user_name = form.username_new.data
            db.session.add(current_user)
            db.session.commit()
            flash('已修改用户名')
            return redirect(url_for('main_bp.index'))
        else:
            flash('此用户名已存在')
    return render_template('auth/change_name.html' ,form=form)


@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main_bp.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('密码已重置，请重新登录')
            return redirect(url_for('auth_bp.login'))
        else:
            flash('发生错误，密码未重置')
            return redirect(url_for('main_bp.index'))
    return render_template('auth/resetpassword.html', form=form)


@auth_bp.route('/reset', methods=['GET', 'POST'])
def forget_password():
    # 表示匿名用户的特殊用户对象，返回True ，普通用户False
    if not current_user.is_anonymous:
        return redirect(url_for('main_bp.index'))
    form = ForgetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.user_name == form.username.data:
            token = user.generate_password_token()
            send_email(user.email, '重置密码', 'auth/email/forget', user=user, token=token)
            flash('已发送重置链接到指定邮箱， 请注意查收')
            return redirect(url_for('auth_bp.login'))
    return render_template('auth/forgetpassword.html', form=form)


@auth_bp.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    new_email = form.email.data
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            try:
                # 修改的邮箱是否已经被注册过
                form.validate_email(form.email)
            except:
                return False
            token = current_user.generate_change_email_token(new_email)
            send_email(new_email, "更换邮箱", 'auth/email/change_email', user=current_user, token=token)
            flash('已发送确认链接到新邮箱，请查收')
            return redirect(url_for('main_bp.index'))
    return render_template('auth/change_email.html', form=form)


@auth_bp.route('/change-email/<token>')
@login_required
def change_email_confirm(token):
    if current_user.confirm_new_email(token):
        db.session.commit()
        flash(f'邮箱已替换为{current_user.email}')
    else:
        flash('邮箱替换失败')
    return redirect(url_for('main_bp.index'))

