from flask import render_template, redirect,\
    url_for, abort,flash, request, current_app, make_response
from datetime import datetime
from . import main_bp
from ..models import User, Permission, Post, AnonymousUser
from .forms import NameForm, EditProfileForm,\
    EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..email import send_email
import logging
from flask_login import login_required, current_user
from ..decorators import admin_required,permission_required
from ..models import Role, User, Comment
from flask_sqlalchemy import get_debug_queries
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
    # 根据cookies show_follow决定显示所有posts还是关注对象的posts
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed :
        query = current_user.idol_posts
    else:
        query = Post.query
    
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           pagination=pagination, show_followed=show_followed)

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
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)

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
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form,user=user)

# 为blog提供固定的链接
# 添加评论功能
@main_bp.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        # 数据库需要的是真正的user对象，current_user是上下文代理对象，是user的轻度包装
        comment = Comment(body=form.body.data, post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('评论成功')
        # 重定向到最后一页评论，显示刚提交的评论
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        # 计算当前有多少页的评论
        page = (post.comments.count()-1) // (current_app.config['FLASK_COMMENT_PER_PAGE']) + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).\
        paginate(page, per_page=current_app.config['FLASK_COMMENT_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)

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

# 关注和取消关注
@main_bp.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(user_name=username).first()
    if user is None:
        flash('无效用户')
        return False
    if current_user.is_following(user):
        flash("该用户已在您的关注列表！")
        # 回到之前的该用户个人信息界面
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f"成功关注用户{username}")
    return redirect(url_for('.user', username=username))

@main_bp.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(user_name=username).first()
    if user is None:
        flash('无效用户')
        return False
    if not current_user.is_following(user):
        flash("您没有关注此用户！")
        # 回到之前的该用户个人信息界面
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f"取消关注用户{username}")
    return redirect(url_for('.user', username=username))

# 显示该用户的fans
@main_bp.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(user_name=username).first()
    if user is None:
        flash('无此用户')
        return redirect(url_for('.index'))
    # 从url直接获取参数page=页数
    page = request.args.get('page',1, type=int)
    pagination = user.fans.paginate(
        page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
        error_out=False)
    # pagination.items 是当期page下所有fans
    follows = [{'user':item.fans, 'timestamp':item.timestamp}\
               for item in pagination.items if item.fans != user]
    return render_template('followers.html', follows=follows,user=user,
                           titile="Followers of", endpoint='.followers',
                           pagination=pagination)
# 显示该用户的关注列表
@main_bp.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(user_name=username).first()
    if user is None:
        flash('无此用户')
        return redirect(url_for('.index'))
    # 从url直接获取参数page=页数
    page = request.args.get('page',1, type=int)
    pagination = user.idol.paginate(
        page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
        error_out=False)
    # pagination.items 是当期page下所有fans
    follows = [{'user':item.idol, 'timestamp':item.timestamp}\
               for item in pagination.items if item.idol != user]
    return render_template('followers.html', follows=follows,user=user,
                           titile="Followed by", endpoint='.followed_by',
                           pagination=pagination)

@main_bp.route('/all')
@login_required
def show_all():
    # cookie 只能在响应对象中设置
    # Sometimes it is necessary to set additional headers in a view
    # 要使用make_response 创建响应对象
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp

@main_bp.route('/followed')
@login_required
def show_followed():
    # Sometimes it is necessary to set additional headers in a view
    resp = make_response(redirect(url_for('.index')))
    # 设定cookie  （cookie名称，值，过期时间）
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp

#  管理评论,moderate.html设置是否渲染moderate->comments.html+显示管理评论功能
@main_bp.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).\
        paginate(page,per_page=current_app.config['FLASK_COMMENT_PER_PAGE'],
                 error_out=False)
    comments=pagination.items
    return render_template('moderate.html', pagination=pagination, comments=comments, page=page)

# 显示或隐藏评论
@main_bp.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    # 回到当前评论所处页
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))

@main_bp.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    # 回到当前评论所处页
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))

@main_bp.route('/shutdown')
def server_shutdown():
    """关闭服务器"""
    # 只在测试时使用这个路由
    if not current_app.testing:
        abort(404)
    # 获取Werkzeug对环境开发的关闭函数
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'

# 每次请求之后执行，在main之外的请求也可执行
@main_bp.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASK_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(f'Slow query:{query.statement}\nParameters:{query.parameters}\n'
                                       f'Duration:{query.duration}\nContent:{query.context}\n')
    return response