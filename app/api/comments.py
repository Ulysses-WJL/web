from . import api_bp
from ..models import Post, Permission, Comment
from flask import jsonify,request,g, url_for, current_app
from .decorators import permission_required
from .. import db
from .errors import forbidden

@api_bp.route('/comments/')
def get_comments():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.paginate(page=page, per_page=current_app.config['FLASK_COMMENT_PER_PAGE'],
                                        error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api_bp.get_comments', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api_bp.get_comments', page=page+1)
    return jsonify({'comments': [comment.to_json() for comment in comments],
                    'prev': prev,
                    'next': next,
                    'comments_count': pagination.total})


# 根据comment的id 获取具体的评论
@api_bp.route('/comments/<int:id>')
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())


# 根据post 获取它的所有评论
@api_bp.route('/posts/<int:id>/comments/', methods=['GET'])
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASK_COMMENT_PER_PAGE'], error_out=False)
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('.get_post_comments', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('.get_post_comments', id=id, page=page+1)
    return jsonify({'comments': [comment.to_json() for comment in comments],
                    'prev': prev,
                    'next': next,
                    'count': pagination.total})

# 生成新的post
@api_bp.route('/posts/<int:id>/comments/', methods=['POST'])
@permission_required(Permission.COMMENT)
def new_post_comment(id):
    post = Post.query.get_or_404(id)
    comment = Comment.from_json(request.json)
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201,\
           {'Location': url_for('api_bp.get_comment', id=comment.id)}