from . import api_bp
from ..models import Post, Permission, Comment
from flask import jsonify,request,g, url_for,current_app
from ..decorators import permission_required
from .. import db
from .errors import forbidden
# 获取posts列表， GET请求
# 分页
@api_bp.route('/posts/')
def get_posts():
    page = request.args.get('page', 1, type=int)
    
    pagination = Post.query.paginate(page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'],
                                error_out=False)
    posts = pagination.items
    prev = None
    # 前一页, 后一页的url
    if pagination.has_prev:
        prev = url_for('api_bp.get_posts', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api_bp.get_posts', page=page+1)
    return jsonify({'posts':[post.to_json() for post in posts],
                    'prev_url': prev,
                    'next_url': next,
                    'count': pagination.total})

# 获取某一篇post
@api_bp.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify({'post':post.to_json()})

# 生成一份新的post， POST方式
@api_bp.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE)
def new_post():
    post = Post.from_json(request.json)
    # 数据库中posts表没有author字段，不需要_get_current_object
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    # 201 成功创建, 并设置响应（response）Location首部设置为 获取这个新的post，即重定向到新的URI
    return jsonify(post.to_json()), 201, \
           {"Location": url_for('api_bp.get_post', id=post.id)}

# PUT请求， 修改现有资源
@api_bp.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and\
        not g.current_user.can(Permission.WRITE):
            return forbidden('has no right')
    # 根据 请求中的信息 修改body
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())

