from . import api_bp
from flask import current_app, url_for, jsonify, request
from ..models import User, Post
from .. import db

@api_bp.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())

@api_bp.route('/users/<int:id>/posts')
def get_user_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.comments.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_pre:
        prev = url_for('api_bp.get_user_posts', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api_bp.get_user_posts', id=id, pahe=page+1)
    return jsonify({'posts': [post.to_json() for post in posts],
                    'prev':prev,
                    'next':next,
                    'posts_count':pagination.total})

# 获取用户所关注对象的所有post
@api_bp.route('/user/<int:id>/timeline')
def get_user_idol_post(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.idol_posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_pre:
        prev = url_for('api_bp.get_user_posts', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api_bp.get_user_posts', id=id, pahe=page+1)
    return jsonify({'posts': [post.to_json() for post in posts],
                    'prev':prev,
                    'next':next,
                    'post_count': pagination.total})