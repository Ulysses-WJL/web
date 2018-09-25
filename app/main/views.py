from flask import render_template, redirect,\
    url_for, abort,flash, request, current_app
from datetime import datetime
from . import main_bp
from ..models import User, Permission, Post, AnonymousUser
from .forms import NameForm, EditProfileForm,\
    EditProfileAdminForm, PostForm
from .. import db
from ..email import send_email
import logging
from flask_login import login_required, current_user
from ..decorators import admin_required
from ..models import Role, User
logging.basicConfig(format="%(asctime)s%(message)s", level=logging.INFO)


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        # 创建一个post时传入user实例对象，方便操作
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    # 将所有的文章按时间降序排列
    # posts = Post.query.order_by(Post.timestamp.desc()).all()
    # 从url中获取参数 ？page=1， 默认获取第一页，获取的数据为int型
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           pagination=pagination)

# def index():
#     # name = None
#     form = NameForm()
#     # Call :meth:`validate` only if the form is submitted.
#     #  This is a shortcut for ``form.is_submitted() and form.validate()``.
#     # 当表单被提交时，调用验证函数， 返回 是否提交了表单&内容是否为空
#     if form.validate_on_submit():
#         # name = form.name.data # 表单的数据，空则为''
#         user = User.query.filter_by(user_name=form.name.data).first()
#         if user is None:
#             user = User(user_name=form.name.data)
#             user.password = '123456'
#             db.session.add(user)
#             db.session.commit()
#             session['know'] = False
#             # flask 邮件发送
#             # ogging.info(f"admin:{app.config['FLASK_ADMIN']}, user: {user}, sender:{mail_user}")
#             if current_app.config['FLASK_ADMIN']:
#                 # 向admin（2276777056@qq.com）发送邮件
#                 logging.info(f"admin: {current_app.config['FLASK_ADMIN']}, user:{user}")
#                 send_email(current_app.config['FLASK_ADMIN'], 'New User', 'mail/new_user', user=user)
#         else:
#             session['know'] = True
#         session['name'] = form.name.data
#         form.name.data = ''
#         return redirect(url_for('main_bp.index'))  # 提交数据后，回到index页面，数据被保存在session中
#         # form.name.data = ''
#     # 渲染模板
#     return render_template(
#         'index.html',
#         url=url_for(
#             'static',
#             filename='favicron.ico'),
#         form=form,
#         name=session.get('name'),
#         current_time=datetime.utcnow(),
#         know=session.get('know', False))
#     # 静态文件favicron.ico

# 展示用户信息
@main_bp.route('/user/<username>')
def user(username):
    user = User.query.filter_by(user_name=username).first_or_404()
    if user is None:
        abort(404)
    # 在user信息内显示自己发布的blog信息
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)

@main_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        # 真实姓名
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('已更新用户信息')
        # user_name 注册时使用的名字
        return redirect(url_for('.user', username=current_user.user_name))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)

# administrator修改个人信息， 需要admin权限
@main_bp.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.user_name = form.user_name.data
        user.confirmed = form.confirmed.data
        # form.role.data 获取的是role.id,
        # EditProfileAdminForm self.role.choices 决定标识符为id，显示文本为name
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('已更新用户信息')
        return redirect(url_for('.user', username=user.user_name))
    form.email.data = user.email
    form.user_name.data = user.user_name
    form.confirmed.data = user.confirmed
    form.role.data = user.role
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form,user=user)

# 为blog提供固定的链接
@main_bp.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])

# 在post下点击edit 进入编辑
@main_bp.route('/edit/<int:id>', methods=['GET', "POST"])
@login_required
def edit_post(id):
    # 获取当前post对象
    post = Post.query.get_or_404(id)
    # 不是管理员修改，也不是当前post所有者在修改
    if current_user != post.author and\
        not current_user.can(Permission.ADMIN):
            abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash("已修改post")
        return redirect(url_for('.edit_post', id=post.id))
    form.body.data = post.body
    return  render_template('edit_post.html', form=form)